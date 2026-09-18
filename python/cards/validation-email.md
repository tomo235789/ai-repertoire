---
id: validation-email
lang: python
title: メールアドレスの形式を検証する
tags: [メールアドレス, 形式チェック, バリデーション, email, format, validate, pydantic]
lib: pydantic
fn: EmailStr
since: "2.0"
verified: 2026-09-17
status: public
---

文字列がメールアドレスの構文かを email-validator で検証し、ドメインを小文字化した正規形で返す。追加パッケージ `email-validator` が必要（`pip install "pydantic[email]"`）。

## Signature

```python
pydantic.EmailStr  # フィールド型として使う。str のサブクラスではなく検証用の型
```

## Usage

```python
from pydantic import BaseModel, EmailStr, TypeAdapter

class Signup(BaseModel):
    email: EmailStr

Signup(email="User@Example.COM").email  # => 'User@example.com'（ドメインだけ小文字化）
TypeAdapter(EmailStr).validate_python("user@localhost")
# => raises ValidationError（value_error: The part after the @-sign is not valid. It should have a period.）
```

## Contract

- 文字列以外は `string_type`、構文が合わなければ `value_error`（`msg` は `value is not a valid email address: 理由`）で失敗する。値は `str` のまま返る（`EmailStr` 自体はインスタンス化できない検証用の型）
- 正規化する。ドメイン部は小文字化（`User@Example.COM` → `User@example.com`）、ローカル部はそのまま、前後の空白と改行は除去、Punycode ドメインは Unicode に戻す（`user@xn--r8jz45g.jp` → `user@例え.jp`）
- 通る例: `user@example.com`、`first.last+tag@example.co.jp`、`a@b.c`、`user@sub.example.com`、`ユーザー@example.com`、`user@例え.jp`（国際化アドレスは既定で許可）
- 通らない例: `user@localhost`、`user@example`（ドメインにピリオドが必要）、`user@127.0.0.1`、`user@[192.168.0.1]`、`"quoted"@example.com`、`.user@example.com`、`user..dot@example.com`、`user@exa_mple.com`、`user@example-.com`、`user name@example.com`、`""`
- `check_deliverability` は常に `False`。DNS 引きはせず、存在しないドメイン（`user@thisdomaindoesnotexist.example`）も通る
- `strict=True` でも同じ検証・正規化が走る
- `NameEmail` は `Alice <alice@example.com>` 形式を `name` / `email` に分けて受ける。`alice@example.com` だけなら `name` はローカル部。`str()` で `Alice <alice@example.com>` に戻り、`model_dump_json` もその形
- 関数として使うなら `pydantic.validate_email(value)` が `(name, normalized_email)` のタプルを返す

## Alternatives

- 正規表現の簡易チェックで十分なら `Annotated[str, Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")]`（依存を増やさない）
- 到達可能かまで見たいなら `email_validator.validate_email(s, check_deliverability=True)` を直接呼ぶ（DNS 引きが走る）
- pydantic を使わないなら `email_validator.validate_email(s).normalized` を直接呼ぶ（`EmailStr` の中身と同じ）

## Pitfalls

- zod の `z.email()` は値を変換しないが、`EmailStr` はドメインを小文字化し前後の空白を落とす。保存した値と入力の `==` 比較が食い違う
- zod は `a@b.c`（1 文字 TLD）を拒否するが `EmailStr` は通す。一方 `user@localhost` は両方とも既定で拒否し、`EmailStr` には zod の `pattern` のような差し替え口が無い。ローカル環境用の値は別の型（`str`）で受ける
- `email_validator` が無いと `ImportError`。本番イメージでも `pydantic[email]` を入れる
- 重複判定に使うなら注意。ローカル部は大文字小文字を保つ（`USER@example.com` と `user@example.com` は別の文字列）ので、必要なら `.lower()` を別途かける

## Test

`examples/validation-email_test.py`
