---
id: validation-coerce-number
lang: python
title: 文字列などの入力を数値に変換して検証する
tags: [数値変換, 型変換, クエリ文字列, coerce, number, cast, pydantic]
lib: pydantic
fn: TypeAdapter
since: "2.0"
verified: 2026-09-17
status: public
---

クエリ文字列や環境変数のように文字列で届く値を、pydantic の lax モードで `int` / `float` にしてから範囲などを検証する。モデルを定義せずに型 1 つだけ検証したいときは `TypeAdapter` を使う。

## Signature

```python
TypeAdapter(type).validate_python(object, *, strict=None, from_attributes=None, context=None)
```

## Usage

```python
from typing import Annotated
from pydantic import Field, TypeAdapter, ValidationError

Port = TypeAdapter(Annotated[int, Field(ge=1, le=65535)])
Port.validate_python("8080")  # => 8080
Port.validate_python("")      # => raises ValidationError（type: int_parsing）
Port.validate_python("0")     # => raises ValidationError（type: greater_than_equal）
TypeAdapter(int).validate_python("12.0")  # => 12
TypeAdapter(float).validate_python("1e3")  # => 1000.0
```

## Contract

- `int` の lax モードは、10 進整数の文字列（前後の空白・符号・`_` 区切り・先頭の 0 を許す）、小数部が 0 の `float` / `Decimal` / 文字列（`12.0` → 12、`"12.0"` → 12）、`bool`（`True` → 1）、`bytes`（`b"12"` → 12）を `int` に変換する
- `int` で失敗する入力: `""` / `"  "`（`int_parsing`）、`"12.5"` / `"1e3"` / `"0x10"` / `"abc"` / 全角数字（`int_parsing`）、`12.5`（`int_from_float`）、`nan` / `inf`（`finite_number`）、`None` / `[]`（`int_type`）
- `float` の lax モードは `"12"` → 12.0、`"1e3"` → 1000.0、`" 1.5 "` → 1.5、`"1_000.5"` → 1000.5、`True` → 1.0 に変換する。`"inf"` / `"nan"` / `"Infinity"` は既定で通る（`Field(allow_inf_nan=False)` で `finite_number` の失敗にできる）。`""` / `"0x10"` / `"abc"` は `float_parsing`、`None` は `float_type` で失敗する
- `strict=True` を渡すか `Annotated[int, Field(strict=True)]` にすると変換しない。`"12"` / `12.0` / `True` はすべて `int_type` で失敗する
- 桁数の上限は無い。`"99999999999999999999999999"` はそのまま多倍長 `int` になる
- `Field(ge=, le=, gt=, lt=, multiple_of=)` の制約は変換後の値に対して行う。失敗の `type` は `greater_than_equal` / `less_than_equal` など
- `int | None` にすると `None` はそのまま通るが、`""` は `int_parsing` で失敗する（zod の `optional` と違い、空文字は `None` に寄せない）
- 失敗は `ValidationError`（カード validation-safe-parse）。`validate_json('"12"')` / `validate_strings("12")` でも同じ変換規則

## Alternatives

- 例外の型より軽さを優先するなら `int(s)`（`ValueError`。`"12.0"` は失敗、`" 12 "` は通る）や `float(s)`
- モデルの中では `age: int` と書くだけで同じ変換が走る（カード validation-parse-schema）
- 他ライブラリでは msgspec（`msgspec.convert(s, int, strict=False)`）。ここでは名前のみ

## Pitfalls

- zod の `z.coerce.number()` は `Number()` 変換なので `''` / `null` / `false` が 0 になり、`'0x10'` / `'1e3'` が通る。pydantic の `int` はこれらをすべて拒否し、`bool` だけ `True` → 1 に変換する。空文字を「未指定」にしたいなら受け取る側で `if s == "": None` と分岐する
- `"12.0"` と `12.0` が `int` として通る。「整数の文字列だけ」を受けたいなら `Annotated[str, Field(pattern=r"^\d+$")]` で文字列側を絞ってから `int()` する
- `bool` が数値に変換される（`True` → 1）。`bool` を弾きたいなら `strict=True`
- `float` の既定は `"nan"` / `"inf"` を通す。JSON に出したり比較に使ったりするなら `Field(allow_inf_nan=False)` を付ける
- `TypeAdapter` の生成はスキーマ構築のコストがかかる。関数の中で毎回作らず、モジュールレベルで 1 回作る

## Test

`examples/validation-coerce-number_test.py`
