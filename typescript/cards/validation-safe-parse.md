---
id: validation-safe-parse
lang: typescript
title: 入力データを例外を投げずに検証して結果オブジェクトで受け取る
tags: [例外を投げない検証, 結果型, バリデーション, safeParse, result, validate, zod]
lib: zod
fn: safeParse
since: "4.0"
verified: 2026-09-17
status: public
---

スキーマ検証の成否を `{ success, data }` / `{ success, error }` の判別共用体で受け取る。フォーム入力やリクエストボディのように、失敗が正常系の一部である場面で使う。

## Signature

```ts
schema.safeParse(data: unknown): { success: true; data: T } | { success: false; error: ZodError }
```

## Usage

```ts
import { z } from 'zod';

const User = z.object({ name: z.string(), age: z.number() });
const result = User.safeParse({ name: 'alice', age: '20' });
if (result.success) {
  result.data; // { name: string; age: number }
} else {
  result.error.issues; // [{ code: 'invalid_type', path: ['age'], message: '...' }]
  z.prettifyError(result.error); // '✖ Invalid input: expected number, received string\n  → at age'
}
```

## Contract

- 検証の失敗では例外を投げず、`success: true` なら `data`、`success: false` なら `error`（`ZodError`）を持つオブジェクトを返す。`success` で分岐すると `data` / `error` の型が確定する（もう一方は `never`）
- 成功時のオブジェクトに `error` キーは無く、失敗時に `data` キーは無い（`'data' in result` は `false`）
- 値の変換規則は `parse` と同じ。未知キーは除去され、返り値は新しいオブジェクトで、入力は変更されない
- `z.treeifyError(error)` はパス構造のツリー（`{ errors: [], properties: { age: { errors: [...] } } }`）、`z.flattenError(error)` は `{ formErrors, fieldErrors }`、`z.prettifyError(error)` は複数行の文字列を返す
- 非同期の `refine` / `transform` を含むスキーマでは同期 `safeParse` が `$ZodAsyncError` を投げる（`success: false` にはならない）。`safeParseAsync` を使う
- `.transform()` / `.refine()` の中で投げた例外は捕捉されず、そのまま伝播する

## Alternatives

- 失敗を例外にしてよいなら `parse`（カード validation-parse-schema）
- 他ライブラリでは valibot（`v.safeParse`）、ajv（`validate()` の真偽値 + `errors`）。ここでは名前のみ

## Pitfalls

- `success` を見ずに `result.data` を使うと型は `T | undefined` になる。必ず `if (result.success)` で絞ってから使う
- `ZodError.message` は `issues` の JSON 文字列で長い。UI やログには `z.prettifyError` / `z.flattenError` を使う
- `error.format()` / `error.flatten()` メソッドも残っているが、zod 4 では `z.treeifyError` / `z.flattenError` のトップレベル関数が主。新規コードでは関数側を使う
- 「例外を投げない」のはスキーマ検証の失敗だけ。非同期スキーマの同期呼び出しや `transform` 内の例外は投げる

## Test

`examples/validation-safe-parse.test.ts`
