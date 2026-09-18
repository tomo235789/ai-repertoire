---
id: error-cause-chain
lang: python
title: エラーに原因を付けて包み直す
tags: [原因の連鎖, 例外のラップ, 文脈の追加, 根本原因, cause, raise-from, exception-chaining, root-cause]
lib: stdlib
fn: raise from
since: "3.0"
verified: 2026-09-17
status: public
---

下位の例外を `__cause__` に載せて上位の文脈を持つ例外を投げ直す。「何をしていて失敗したか」と「なぜ失敗したか」を両方 traceback に残すために使う。

## Signature

```python
raise NewError("message") from original_exception
```

## Usage

```python
class ConfigError(Exception): ...

def load(text: str) -> int:
    try:
        return int(text)
    except ValueError as err:
        raise ConfigError(f"設定を読めなかった: {text!r}") from err  # __cause__ に元の例外が付く

try: load("x")
except ConfigError as e: repr(e.__cause__)  # => "ValueError(\"invalid literal for int() with base 10: 'x'\")"
```

## Contract

- `raise X from err` は `X.__cause__ = err`、`X.__suppress_context__ = True` にする。traceback には元の例外の後に **"The above exception was the direct cause of the following exception:"** を挟んで両方表示される
- `except` の中で `from` 無しに `raise X` すると `__cause__` は `None` のまま `__context__` に処理中の例外が自動で入り、traceback は **"During handling of the above exception, another exception occurred:"** になる。`from` を付けたときも `__context__` は同じく設定される
- `raise X from None` は `__cause__` を `None`、`__suppress_context__` を `True` にし、traceback に元の例外を表示しない（`__context__` には残る）
- `from` の右辺は例外インスタンスか例外クラス（クラスなら引数無しでインスタンス化される）か `None`。それ以外は `TypeError`（`exception causes must derive from BaseException`）
- `except` の外でも `raise X from err` は使える（`__context__` は `None`）
- `traceback.format_exception(e)` は連鎖全体を文字列のリストで返す。`chain=False` なら最後の例外だけ。根本原因は `while e.__cause__ is not None: e = e.__cause__` で辿る

## Alternatives

- 文脈だけ足して同じ例外を投げ直すなら `err.add_note("while loading config"); raise`（3.11）。型も traceback も元のまま
- 複数の原因（並列処理で複数失敗）をまとめるなら `ExceptionGroup`（カード error-aggregate）
- ログに出す形に展開するのはカード log-structured（`logging.exception` は連鎖ごと出力する）

## Pitfalls

- TypeScript の `cause` は任意の値だが、Python の `from` は例外（か `None`）だけ。文字列を渡すと `TypeError`
- TypeScript には暗黙の連鎖が無いが、Python は `except` 内で投げると `from` 無しでも `__context__` が付き "During handling ..." が出る。意図した原因なら `from err`、無関係なら `from None` で意図を明示する
- `from None` は原因を隠す。ユーザー向けメッセージを整えるとき以外は使わず、ログには残す
- `raise ConfigError(str(err))` を `except` の中で書くと `__context__` と元の traceback は残るが、`__cause__`（明示的な因果）は設定されない。原因を明示するなら `raise ConfigError(str(err)) from err` と書く
- `__cause__` と `__context__` は別物。`from` を付けても `__context__` は消えないので、辿るときはどちらを見るか決める（原因の連鎖は `__cause__`）

## Test

`examples/error-cause-chain_test.py`
