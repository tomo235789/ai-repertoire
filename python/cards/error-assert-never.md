---
id: error-assert-never
lang: python
title: 分岐の網羅漏れをコンパイル時に検出する
tags: [網羅性チェック, 分岐漏れ, リテラル型, match, exhaustive, assert_never, Never, discriminated-union]
lib: stdlib
fn: typing.assert_never
since: "3.11"
verified: 2026-09-17
status: public
---

`match` の `case _:` で `assert_never(x)` を呼び、`Literal` / `Enum` / ユニオン型のケースを全部処理していなければ型検査器（mypy / pyright）がエラーにする。列挙子を足したときの処理漏れを防ぐために使う。

## Signature

```python
typing.assert_never(arg: Never, /) -> Never
```

## Usage

```python
from typing import Literal, assert_never

Kind = Literal["circle", "square"]

def area(kind: Kind, size: float) -> float:
    match kind:
        case "circle": return 3.14159 * size ** 2
        case "square": return size ** 2
        case _: assert_never(kind)  # Kind に "triangle" を足すと型検査器がここでエラーにする
area("circle", 1.0)  # => 3.14159
```

## Contract

- 引数の型が `Never`。`match` / `if` で全ケースを処理し切ると `case _:` での `kind` は `Never` に絞り込まれ、型検査が通る。ケースが残っていると残りの型（`Literal['triangle']` など）が `Never` に代入できずエラーになる。戻り値も `Never` なので「すべてのパスで値を返す」検査も満たす
- 実行時に呼ばれたら（`cast` や JSON など型を通らない値が来た場合）`AssertionError('Expected code to be unreachable, but got: <repr>')` を投げる。`repr` は 100 文字で切られる
- 中身は `raise AssertionError(...)` であって `assert` 文ではないので、**`python -O` でも消えない**
- 網羅漏れを **静的に** 検出するのは型検査器だけで、CI で `mypy` か `pyright` を回す必要がある。実行時は `assert_never` に届いた時点で `AssertionError` になるので、その分岐を通すテストがあれば pytest でも気づける
- `match` の `case` に `return` があれば、`case _:` の後に到達しないことも型検査器が理解する。`if / elif / else` の `else` でも同じように使える
- 3.10 以前は `typing_extensions.assert_never`。`Never` 型も同じく `typing_extensions` にある

## Alternatives

- `case _:` を置かず `match` の網羅性を型検査器に任せることもできる（pyright は `reportMatchNotExhaustive`、mypy は `--enable-error-code exhaustive-match`）。実行時に届いた不正値では何も起きないので `assert_never` の方が安全
- `Enum` のときは `for` で全メンバーを処理する辞書 `{Kind.CIRCLE: ..., Kind.SQUARE: ...}` にすると、キー不足は実行時の `KeyError` でしか分からない。分岐で書いて `assert_never` を使う
- 実行時にも型で弾きたいなら入口でスキーマ検証（カード http-fetch-json-typed）

## Pitfalls

- TypeScript は `tsc` が無いと検出できないのと同じで、Python も **型検査器を動かしていなければ何も検出しない**。`assert_never` を置いただけで安心しない
- `str` のような開いた型は絞り込んでも `Never` にならない。`Literal[...]` / `Enum` / クラスのユニオンにする
- `case "circle" | "square":` のようにまとめると絞り込みは効く。`case str():` のような広いパターンを先に書くと以降が到達不能になり、逆に型検査器の警告が出る
- `assert_never` の引数に別の変数を渡すと意味が無い。`match` の対象そのもの（絞り込まれた変数）を渡す
- `case _: raise ValueError(kind)` だけだと `Never` の検査が無く、列挙子を足しても気付けない

## Test

`examples/error-assert-never_test.py`
