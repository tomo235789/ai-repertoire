---
id: error-aggregate
lang: python
title: 複数のエラーを 1 つにまとめる
tags: [複数エラー, 例外の集約, まとめて報告, 並列失敗, ExceptionGroup, except-star, TaskGroup, multiple-errors]
lib: stdlib
fn: ExceptionGroup
since: "3.11"
verified: 2026-09-17
status: public
---

複数の例外を `exceptions` に持つ 1 つの例外として投げ、受け側は `except*` で型ごとに取り出す。並列処理の失敗をまとめて報告したり、`asyncio.TaskGroup` が投げるグループを扱うのに使う。

## Signature

```python
ExceptionGroup(message: str, exceptions: Sequence[Exception])
```

## Usage

```python
errors: list[Exception] = []
for url in ["https://example.com/a", "https://example.com/b"]:
    try: fetch(url)
    except OSError as err: errors.append(err)
if errors:
    raise ExceptionGroup(f"{len(errors)} 件の取得に失敗", errors)
# 受け側:
#   try: ...
#   except* ConnectionError as group: print(group.exceptions)  # => 該当する例外だけのタプル
#   except* TimeoutError as group: ...                         # 両方の節が実行され得る
```

## Contract

- `ExceptionGroup(message, [e1, e2])` は `Exception` のサブクラス。`.message` と `.exceptions`（渡した列を **タプルにコピー** したもの）を持ち、`str(eg)` は `'message (2 sub-exceptions)'`
- `exceptions` は空だと `ValueError`。要素は `Exception` のインスタンスに限られ、`KeyboardInterrupt` などを入れると `TypeError`。それらを含めるなら `BaseExceptionGroup`（要素がすべて `Exception` なら自動で `ExceptionGroup` になる）
- `except* T as group` は **`T` に合う例外だけを集めた新しいグループ** を `group` に渡す（入れ子構造と `message` は保たれる）。合う節がすべて実行され、どの節にも合わなかった残りは自動で投げ直される
- 普通の `except ValueError` はグループを捕捉しない（`ExceptionGroup` は `ValueError` ではない）。`except ExceptionGroup` なら丸ごと捕捉できる
- `group.subgroup(cond)` は条件に合う例外だけのグループ（無ければ `None`）、`group.split(cond)` は `(合う, 合わない)` の組を返す。`cond` は例外型・型のタプル・述語関数
- `except*` の中では `return` / `break` / `continue` が使えない（`SyntaxError`）。`except*` は単独の例外（グループでないもの）も `ExceptionGroup('', (e,))` に包んで捕捉する
- `asyncio.TaskGroup` は失敗したタスクの例外を `ExceptionGroup`（message `'unhandled errors in a TaskGroup'`）にまとめて投げる。traceback はツリー状（`+-+---- 1 ----`）で表示される

## Alternatives

- 3.10 以前は `exceptiongroup` パッケージ（`from exceptiongroup import ExceptionGroup`。`except*` の代わりに `catch({ValueError: handler})`）
- 最初の失敗で止めてよいなら `asyncio.gather(..., return_exceptions=False)`（最初の例外がそのまま伝わる。残りのタスクは自動ではキャンセルされず走り続けるので、止めたいなら `TaskGroup` を使うか自分でキャンセルする）
- 検証エラーの一覧のように「例外でない値の列」で足りるなら `Result` のリスト（カード result-try-to-result）

## Pitfalls

- TypeScript の `AggregateError.errors` は任意の値の配列だが、`ExceptionGroup.exceptions` は例外だけのタプル。文字列を入れるには `Exception` に包む
- `except ValueError` で `ExceptionGroup` は止まらない。`TaskGroup` を使い始めたコードで既存の `except` が効かなくなる典型。`except*` に書き換えるか `except ExceptionGroup` を足す
- `except*` の節では `return` できない。関数の戻り値を決めたいなら結果を変数に入れて節の外で `return` する
- `str(group)` は件数しか分からない。ログには `group.exceptions` を展開する（`logging.exception` は traceback をツリーで出す）
- `exceptions` が 1 件でもグループ。「1 件なら素の例外を投げる」と分岐すると受け側の型が 2 通りになるので、常にグループで投げる

## Test

`examples/error-aggregate_test.py`
