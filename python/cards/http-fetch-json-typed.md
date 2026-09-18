---
id: http-fetch-json-typed
lang: python
title: HTTP レスポンスの JSON を型付きで受け取る
tags: [JSON 取得, レスポンス検証, 型付け, スキーマ, httpx, json, pydantic, parse]
lib: pydantic
fn: model_validate_json
since: "2.0"
verified: 2026-09-17
status: public
---

`raise_for_status()` でエラー応答を弾いてから、本文のバイト列を `Model.model_validate_json` に通して型の付いたモデルを得る。外部 API の応答を `dict` のまま使わないために使う。

## Signature

```python
Model.model_validate_json(json_data, *, strict=None, context=None, by_alias=None, by_name=None)
```

## Usage

```python
import httpx
from pydantic import BaseModel

class User(BaseModel):
    id: int
    name: str

def fetch_user(client: httpx.Client, user_id: int) -> User:
    r = client.get(f"https://example.com/users/{user_id}").raise_for_status()  # 4xx / 5xx は HTTPStatusError
    return User.model_validate_json(r.content)  # => User(id=1, name='ann')。形が違えば ValidationError
```

## Contract

- httpx は 4xx / 5xx でも `Response` を返す。`raise_for_status()` は 4xx / 5xx で `httpx.HTTPStatusError`（`.response` / `.request` 付き）を投げ、1xx / 2xx / 3xx は **その `Response` を返す** のでメソッドチェーンできる
- `model_validate_json` は `bytes` / `str` / `bytearray` を受け取り、JSON の解析と検証を Rust 側で 1 度に行う。`Model.model_validate(r.json())` より速い（この環境で約 2 倍）
- 成功すると `Model` のインスタンス。未知のキーは既定で無視され、`"1"` → `int` のような緩い変換が効く。`strict=True` で型の一致を要求できる
- 本文が JSON でない（HTML・空・204 No Content）ときは `ValidationError`（`errors()[0]["type"]` が `'json_invalid'`）。フィールドの不一致は同じ `ValidationError` で `loc` にフィールド名が入り、全フィールド分まとめて報告される
- `ValidationError` は `ValueError` のサブクラス。`HTTPStatusError` は `httpx.HTTPError` の系統で別物なので、呼び出し側で区別できる
- `Content-Type` ヘッダは見ない。`text/plain` でも本文が JSON なら成功し、`application/json` でも本文が HTML なら失敗する

## Alternatives

- 配列のトップレベルは `TypeAdapter(list[User]).validate_json(r.content)`
- 例外にしたくなければ `try/except ValidationError` を関数に閉じ込め `None` や `Result` を返す（カード validation-safe-parse）
- 外部ライブラリを増やせないなら `r.json()` の後に `dataclasses` と手書きの検証。速度と検証の網羅は落ちる

## Pitfalls

- TypeScript の zod は `res.json()` の後に `parse` する 2 段階だが、pydantic は `model_validate_json` で 1 段。`r.json()` を経由して `model_validate` に渡すと `JSONDecodeError` と `ValidationError` の 2 種類を扱うことになる
- `r.json()` は本文が JSON でなければ `json.JSONDecodeError`（`ValueError` のサブクラス）。`model_validate_json` なら同じ状況が `ValidationError` に統一される
- `raise_for_status()` を忘れるとエラー応答の `{"error": "..."}` をモデルに通してしまい、原因が「フィールド不足」に見える
- `Content-Type: application/json` でも本文が HTML（ログイン画面・エラーページ）のことがある。`json_invalid` は「サーバーが JSON 以外を返した」として扱う
- `strict=True` を付けないと `"1"` が `int` として通る。数値が文字列で返る API に頼るなら明示し、頼らないなら `strict=True` で早めに気付く

## Test

`examples/http-fetch-json-typed_test.py`
