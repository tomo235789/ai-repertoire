---
id: http-fetch-json-typed
lang: typescript
title: HTTP レスポンスの JSON を型付きで受け取る
tags: [JSON 取得, レスポンス検証, 型付け, スキーマ, fetch, json, zod, parse]
lib: zod
fn: parse
since: "4.0"
verified: 2026-09-17
status: public
---

`res.ok` を確認し、`res.json()` した値を `schema.parse` に通して型の付いた値を得る。外部 API の応答を `any` のまま使わないために使う。

## Signature

```ts
ZodType<Output>.parse(data: unknown): Output
// 成功時は Output（object スキーマは未定義キーを取り除いた新しいオブジェクト）、失敗時は ZodError を throw
```

## Usage

```ts
import { z } from 'zod';

const User = z.object({ id: z.number(), name: z.string() });
type User = z.infer<typeof User>; // { id: number; name: string }
const fetchUser = async (id: number): Promise<User> => {
  const res = await fetch(`https://example.com/users/${id}`);
  if (!res.ok) throw new Error(`HTTP ${res.status}`); // 4xx / 5xx でも fetch は resolve する
  return User.parse(await res.json());                 // 形が違えば ZodError
};
```

## Contract

- `fetch` は 4xx / 5xx でも resolve する。`res.ok`（200〜299）で分岐しないとエラー応答の JSON をスキーマに通してしまう
- `res.json()` は `Content-Type` を見ずに本文を `JSON.parse` する。本文が JSON でなければ `SyntaxError`（`Unexpected token '<', "<html>" is not valid JSON` など）、空なら `Unexpected end of JSON input` で reject する。逆に `text/plain` でも本文が JSON なら成功する
- `schema.parse` は成功すればスキーマの型を持つ値を返す。`z.object` は **未定義のキーを取り除いた新しいオブジェクト** を返す（元の値は変更しない）
- 失敗すると `ZodError`（`Error` のサブクラス、`name` は `'ZodError'`）を throw する。`issues[]` に `path` / `code` / `message` が入り、`z.prettifyError(err)` で人が読める形になる
- 例外にしたくなければ `schema.safeParse(value)` が `{ success: true, data }` / `{ success: false, error }` を返す
- `Response` の本文は 1 回しか読めない。`res.json()` のあとに `res.text()` を呼ぶと `TypeError`（`Body is unusable`）

## Alternatives

- 未定義キーをエラーにするなら `z.object({...}).strict()`、残すなら `.loose()`
- スキーマライブラリを増やせないなら型ガード関数 `(v: unknown): v is User` を自分で書く
- OpenAPI 定義がある API なら `openapi-fetch` + `openapi-typescript` で型を生成する方が保守しやすい

## Pitfalls

- `res.json() as User` はキャストであって検証ではない。API が変わっても実行時に気付けない
- `Content-Type: application/json` でも本文が HTML（エラーページ・ログイン画面）のことがある。`SyntaxError` は「サーバーが JSON 以外を返した」として扱う
- `ZodError.message` は `issues` の JSON 文字列で長い。ログには `z.prettifyError(err)` か `err.issues` を使う
- `z.number()` は文字列の `"1"` を受け付けない。数値が文字列で返る API は `z.coerce.number()` を使う
- 204 No Content や空本文に `res.json()` を呼ぶと `SyntaxError`。ステータスか `Content-Length` で分岐する

## Test

`examples/http-fetch-json-typed.test.ts`
