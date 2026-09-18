---
id: validation-brand-type
lang: python
title: 文字列や数値に名目型を付けて取り違えを防ぐ
tags: [名目型, ブランド型, ID の取り違え防止, brand, nominal-type, NewType, typing]
lib: stdlib
fn: typing.NewType
since: "3.5.2"
verified: 2026-09-17
status: public
---

`str` のままでは区別できない `UserId` と `OrderId` のような値に、型検査器だけが見るタグを付ける。実行時は何もせず、`UserId("u_1")` は素の `str` をそのまま返す。

## Signature

```python
typing.NewType(name, tp)
```

## Usage

```python
from typing import NewType
UserId = NewType("UserId", str)
OrderId = NewType("OrderId", str)

def find(user_id: UserId) -> str:
    return user_id

find(UserId("u_1"))   # => 'u_1'（実行時は素の str のまま）
find("u_1")           # 型検査エラー: str は UserId に代入できない。実行はできる
find(OrderId("o_1"))  # 型検査エラー: OrderId は UserId に代入できない。実行はできる
```

## Contract

- `UserId(x)` は `x` をそのまま返す（`UserId("u_1") is "u_1"` の元オブジェクトと同一、`type()` は `str`）。値の検査も変換もしない。`UserId(3)` も通る
- `UserId` は `typing.NewType` のインスタンスで、`__name__` が `"UserId"`、`__supertype__` が `str`。クラスではないので `isinstance(x, UserId)` は `TypeError`、`class Sub(UserId)` も `TypeError`
- 型検査器（mypy / pyright）は `UserId` を `str` のサブタイプとして扱う。`str` 引数には渡せるが、`str` を `UserId` 引数には渡せない。`UserId` と `OrderId` は互いに代入できない
- `UserId` 同士の演算結果は元の型になる（`UserId("a") + "b"` は `str`）
- `NewType("Nested", UserId)` で重ねられる。`pickle` / `copy` も元の値と同じ
- pydantic は `UserId` を `str` として検証する。`UserId` と `OrderId` を取り違えた入力もそのまま通り、JSON Schema は `{"type": "string"}`

## Alternatives

- 実行時にも区別したいなら `class UserId(str): pass` のサブクラス（`isinstance` が使え、pydantic も別の型として扱う。ただし `+` や `.upper()` の結果は `str` に戻る）
- 値の検証と結び付けるなら `Annotated[str, Field(pattern=r"^u_\d+$")]` を pydantic の型として定義する（カード validation-parse-schema）。ただし名目型にはならない
- 型引数を持つ別名（`Vec = list[float]`）は `TypeAlias` / `type` 文。互換性を切りたいときだけ `NewType`

## Pitfalls

- zod の `brand` は `parse` を通った値だけがブランド型になる（検証と結び付く）が、`NewType` は検証しない。`UserId("")` も `UserId(3)` も通るので、検証は別に書く
- `isinstance(x, UserId)` が `TypeError` になる。実行時の判定は `__supertype__`（`isinstance(x, UserId.__supertype__)`）でしかできず、それは `str` かどうかしか分からない
- pydantic のモデルで `user_id: UserId` と書いても取り違えは検出されない。型検査を CI に入れて初めて意味がある

## Test

`examples/validation-brand-type_test.py`
