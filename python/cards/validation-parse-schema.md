---
id: validation-parse-schema
lang: python
title: 入力データをスキーマで検証して型付きの値に変換する
tags: [スキーマ検証, バリデーション, 型付け, parse, schema, validate, pydantic]
lib: pydantic
fn: BaseModel.model_validate
since: "2.0"
verified: 2026-09-17
status: public
---

外部から来た `dict` を `BaseModel` のサブクラスに通し、合格したら型付きのモデルインスタンスとして受け取る。API レスポンスや設定ファイルの読み込み直後に使う。

## Signature

```python
Model.model_validate(obj, *, strict=None, from_attributes=None, context=None, by_alias=None, by_name=None)
```

## Usage

```python
from pydantic import BaseModel, ValidationError

class User(BaseModel):
    name: str
    age: int

User.model_validate({"name": "alice", "age": "20", "extra": True})
# => User(name='alice', age=20)（"20" は int に変換、未知キー extra は無視）
User.model_validate({"name": 1, "age": "x"})
# => raises ValidationError（errors() に name / age の 2 件）
```

## Contract

- 成功すると `Model` のインスタンスを返す。フィールドの値は入力とは別の新しいオブジェクトで、ネストしたモデル・リストも新しく作られる（`model.tags is src["tags"]` は `False`）
- 入力の `dict` を変更しない。未知キーの除去も型変換も返り値の側だけで起きる
- 失敗すると `ValidationError`（`ValueError` のサブクラス）を投げる。`errors()` に全フィールドの失敗が `dict` のリストでまとまり、最初の 1 件で止まらない。各要素は `type` / `loc`（タプル。ネストは `('addr', 'city')`、リストは `('tags', 1)`）/ `msg` / `input` / `url` を持つ
- スキーマに無いキーは既定で無視する（`model_extra` は `None`）。`model_config = ConfigDict(extra="forbid")` なら `extra_forbidden` で失敗、`extra="allow"` なら `model_extra` に残り `model_dump()` にも含まれる
- 既定は lax モード。`"20"` → 20、`20.0` → 20、`True` → 1、`b"20"` → 20 に変換する。`20.5` は `int_from_float`、`"1e3"` は `int_parsing` で失敗する
- `strict=True` を渡すか `ConfigDict(strict=True)` を付けると型変換しない（`"20"` は `int_type` で失敗）。フィールド単位なら `Annotated[int, Field(strict=True)]`
- `None` / リスト / 文字列など `dict` でもモデルでもない値を渡すと `loc: ()` の `model_type` で失敗する。同じモデルのインスタンスを渡すと再検証せずそのまま返す（`is` で同一）
- 既定値のあるフィールドは欠けていれば補われる。無いと `missing` で失敗する
- `model_dump()` で `dict` に戻る（ネストしたモデルも `dict`、リストは新しいリスト）。`model_validate_json(text)` は JSON 文字列を直接受け、不正な JSON は `json_invalid` の `ValidationError`
- `from_attributes=True` を渡すと属性を持つ任意のオブジェクト（ORM のレコードなど）からも読める

## Alternatives

- 例外を投げたくない場合は `try/except ValidationError`（カード validation-safe-parse）
- モデルを定義せずに `list[int]` のような型だけを検証するなら `TypeAdapter(型).validate_python(data)`（カード validation-coerce-number）
- 他ライブラリでは msgspec（`msgspec.convert`）、attrs + cattrs。ここでは名前のみ

## Pitfalls

- zod の `parse` は未知キーを除去した新しいオブジェクトを返すが、pydantic はモデルインスタンスを返す。`dict` が必要な場面では `model_dump()` を挟む
- zod は既定で型変換しない（`'20'` は `invalid_type`）が、pydantic は既定で lax モードなので `"20"` が 20 として通る。文字列の数値を拒否したければ `strict=True`
- `ValidationError` は `ValueError` のサブクラスなので、`except ValueError` で意図せず握りつぶされる。`except ValidationError` を先に書く
- `errors()` の `url` はドキュメントへのリンクで、ログには冗長。`errors(include_url=False)` で外す
- `Model(**data)` でも同じ検証が走るが、`data` が `dict` でないときに `TypeError` になる。外部入力には `model_validate` を使う

## Test

`examples/validation-parse-schema_test.py`
