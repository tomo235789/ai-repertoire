---
id: error-invariant
lang: python
title: 前提条件を検査して型を絞り込む
tags: [前提条件, 不変条件, 表明, アサーション, 型の絞り込み, invariant, assert, AssertionError]
lib: stdlib
fn: assert
since: "3.0"
verified: 2026-09-17
status: public
---

条件が偽なら `AssertionError` を投げ、真なら以降のコードで条件が成り立つものとして型検査器が型を絞り込む。「ここには来ないはず」というプログラムの前提を明示するために使う。**入力検証には使わない**。

## Signature

```python
assert expression, message
```

## Usage

```python
def total(prices: list[float] | None) -> float:
    assert prices is not None, "prices は呼び出し側で解決済みのはず"  # 偽なら AssertionError
    return sum(prices)  # 型検査器はここで prices を list[float] に絞り込む

def parse_port(text: str) -> int:
    port = int(text)
    if not 0 < port < 65536:  # 外部入力の検証は assert ではなく例外
        raise ValueError(f"port out of range: {port}")
    return port
```

## Contract

- `expression` が偽なら `AssertionError(message)` を投げる。`str(e)` が `message`、`e.args` が `(message,)`。`message` を省くと `str(e)` は `''`。`message` は失敗したときだけ評価される
- **`python -O`（および `PYTHONOPTIMIZE=1`）では `assert` 文ごと削除される**。条件式も `message` も評価されず、`__debug__` が `False` になる。`-OO` も同じ
- 型検査器は `assert x is not None` / `assert isinstance(x, str)` の後で `x` の型を絞り込む（`if` による絞り込みと同じ扱い）。実行時にも同じ条件で `AssertionError` になるので、型と実行の前提が一致する
- `AssertionError` は `Exception` のサブクラス。`except Exception` で捕捉される
- `assert (cond, "msg")` のようにタプルで書くと常に真（非空タプル）で、`SyntaxWarning: assertion is always true, perhaps remove parentheses?` が出る
- `message` には任意の式を書ける（f-string で値を含める）。`AssertionError` のメッセージにそのまま入る

## Alternatives

- 外部入力（引数・API・ファイル）の検証は `if not cond: raise ValueError(...)`。`-O` で消えず、呼び出し側が `except ValueError` で扱える
- 型だけ絞りたく実行時の検査が不要なら `typing.cast(list[float], prices)`。実行時には何もしない
- 型検査器向けの表明だけ欲しいなら `if TYPE_CHECKING: assert prices is not None`（実行時に評価されない）。`typing.assert_type(x, T)`（3.11）は型検査時のみ効く
- 「到達しないはず」の分岐はカード error-assert-never（`-O` でも消えない）

## Pitfalls

- TypeScript の `invariant` は本番でも動くが、Python の `assert` は **`-O` で消える**。Docker イメージや systemd の起動で `python -O` / `PYTHONOPTIMIZE` が付いていると検査が全部無くなる。入力検証・権限チェック・副作用のある式を `assert` に書かない
- `assert` の条件式に副作用（`assert queue.pop()`）を書くと `-O` で実行されなくなる
- `pytest` は `assert` を書き換えて（rewrite）失敗時に値を表示するが、それはテストファイル内だけ。アプリ側の `assert` は通常の `AssertionError`
- `0` / `''` / `[]` が正当な値の変数に `assert value` を使うと弾いてしまう。`assert value is not None` と明示する
- `assert isinstance(x, Foo)` は型の絞り込みには便利だが、ダックタイピングを前提にした呼び出し側を壊す。公開 API の引数には使わない

## Test

`examples/error-invariant_test.py`
