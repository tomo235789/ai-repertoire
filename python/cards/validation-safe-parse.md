---
id: validation-safe-parse
lang: python
title: 入力データを例外を投げずに検証して結果オブジェクトで受け取る
tags: [例外を投げない検証, 結果型, バリデーション, safe-parse, errors, validate, pydantic]
lib: pydantic
fn: ValidationError
since: "2.0"
verified: 2026-09-17
status: public
---

pydantic には zod の `safeParse` に相当する API が無いので、`model_validate` を `try/except ValidationError` で包み、`errors()` のリストを失敗の値として扱う。フォーム入力やリクエストボディのように、失敗が正常系の一部である場面で使う。

## Signature

```python
try: Model.model_validate(data) except ValidationError as e: e.errors(include_url=False)
```

## Usage

```python
from pydantic import BaseModel, ValidationError
class User(BaseModel):
    name: str
    age: int

try:
    user = User.model_validate({"name": "alice", "age": "x"})
except ValidationError as e:
    e.errors(include_url=False)
    # => [{'type': 'int_parsing', 'loc': ('age',), 'msg': 'Input should be a valid integer, ...', 'input': 'x'}]
```

## Contract

- 検証の失敗は `ValidationError`（`ValueError` のサブクラス）1 つに全フィールド分がまとまるので、`except` 節は 1 回しか走らない。成功時は `try` 節の中でモデルインスタンスが得られる
- `e.errors()` は `dict` のリスト。各要素は `type`（`int_parsing` / `missing` / `string_type` など機械判定用の文字列）/ `loc`（フィールドへのパスのタプル。ネストは `('addr', 'city')`、トップレベルの失敗は `()`）/ `msg` / `input` / `url` を持つ。`include_url=False` で `url`、`include_input=False` で `input` を外せる
- `e.error_count()` は失敗の件数、`e.title` はモデル名。`str(e)` は `2 validation errors for User` で始まる複数行の人間向け文字列
- `e.json()` は `errors()` を JSON 文字列にしたもの（`loc` はリストになる）。`e.json(include_url=False)` も可
- 値の変換規則は `model_validate` と同じ。未知キーは無視され、入力は変更されない
- モデルを作らず型だけで検証するなら `TypeAdapter(型).validate_python(data)` を同じ `try/except` で包む。失敗は同じ `ValidationError`
- 型変換の失敗以外（`field_validator` の中で投げた `ValueError` / `AssertionError`）も `ValidationError` に包まれ、`type` が `value_error` / `assertion_error` になる。`TypeError` など他の例外は包まれずそのまま伝わる

## Alternatives

- 失敗を例外にしてよいなら素の `model_validate`（カード validation-parse-schema）
- 成否を値で返す関数にしたいなら `returns.result.safe(exceptions=(ValidationError,))` で包む（カード result-try-to-result）
- 他ライブラリでは msgspec（`msgspec.ValidationError`）、attrs + cattrs。ここでは名前のみ

## Pitfalls

- zod の `safeParse` は `{ success, data | error }` を返すが、pydantic には対応する API が無い。`try/except` で受けるのが公式の作法で、`success` フラグを見て分岐する形にしたいなら自分で `(None, model)` / `(errors, None)` のタプルに詰める
- `except ValueError` でも捕まる（サブクラスのため）。他の `ValueError` と区別するには `except ValidationError` を先に書く
- `errors()` の `msg` は英語の固定文で、`type` が機械判定用。UI の文言は `type` と `loc` から自分で組み立てる
- `e.json()` の既定は `url` を含む。ログや API レスポンスに載せるなら `include_url=False` を付ける

## Test

`examples/validation-safe-parse_test.py`
