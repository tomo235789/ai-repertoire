---
id: validation-email
lang: typescript
title: メールアドレスの形式を検証する
tags: [メールアドレス, 形式チェック, バリデーション, email, format, validate, zod]
lib: zod
fn: z.email
since: "4.0"
verified: 2026-09-17
status: public
---

文字列がメールアドレスの形式かを正規表現で検証する。既定はやや厳しめで、`pattern` オプションで基準を差し替えられる。

## Signature

```ts
z.email(params?: string | { pattern?: RegExp; error?: string }): ZodEmail
```

## Usage

```ts
import { z } from 'zod';

const Email = z.email();
Email.parse('user@example.com');                       // => 'user@example.com'
Email.safeParse('user@localhost').success;             // => false（TLD が必要）
Email.safeParse('user name@example.com').success;      // => false
z.email({ pattern: z.regexes.html5Email }).safeParse('user@localhost').success; // => true
```

## Contract

- 文字列以外は `invalid_type`、形式が合わなければ `invalid_format`（`format: 'email'`、message `Invalid email address`）で失敗する。値は変換せずそのまま返す（小文字化・trim はしない）
- 既定の正規表現（`z.regexes.email`）はローカル部に `A-Za-z0-9_'+-` と区切りの `.`（先頭・末尾・連続は不可）、ドメイン部に英数字とハイフンのラベルと 2 文字以上の英字 TLD を要求する
- 通る例: `user@example.com`、`first.last+tag@example.co.jp`、`USER@EXAMPLE.COM`、`a@b.co`
- 通らない例: `user@localhost`、`user@example`、`a@b.c`、`"quoted"@example.com`、`user@[192.168.0.1]`、`.user@example.com`、`user..dot@example.com`、`user@exa_mple.com`、`ユーザー@example.com`、前後に空白があるもの
- `pattern` で差し替えられる。`z.regexes.html5Email` はブラウザの `<input type="email">` 相当（`user@localhost` や `a@b.c` が通る）、`rfc5322Email` は引用ローカル部や IP リテラルも通す、`unicodeEmail` は非 ASCII を通す
- `.max()` や `.toLowerCase()` などの文字列メソッドを続けて呼べる

## Alternatives

- 正規化して保存するなら `z.email().toLowerCase()`
- 前後の空白を許すなら `z.string().trim().pipe(z.email())`。`z.email().trim()` では検証が先に走って失敗する
- 他ライブラリでは valibot（`v.pipe(v.string(), v.email())`）。ここでは名前のみ

## Pitfalls

- `z.string().email()` は zod 4 で `@deprecated`（動作はする）。新規コードは `z.email()` を使う
- 既定では `user@localhost` や IP リテラルが通らない。開発環境やイントラ用途では `html5Email` に差し替える
- 正規表現による形式チェックにすぎず、`user@example-.com` のような無効なドメインラベルも通る。到達可能かは別に確認する
- 大文字小文字をそのまま返すので、重複判定に使うなら `.toLowerCase()` を付けて揃える

## Test

`examples/validation-email.test.ts`
