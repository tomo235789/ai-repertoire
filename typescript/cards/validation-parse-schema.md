---
id: validation-parse-schema
lang: typescript
title: 入力データをスキーマで検証して型付きの値に変換する
tags: [スキーマ検証, バリデーション, 型付け, parse, schema, validate, zod]
lib: zod
fn: z.object
since: "4.0"
verified: 2026-09-17
status: public
---

外部から来た `unknown` な値をスキーマに通し、合格したら型付きの値として受け取る。API レスポンスや設定ファイルの読み込み直後に使う。

## Signature

```ts
z.object(shape).parse(data: unknown): z.infer<typeof schema>
```

## Usage

```ts
import { z } from 'zod';

const User = z.object({ name: z.string(), age: z.number().int() });
type User = z.infer<typeof User>; // { name: string; age: number }

User.parse({ name: 'alice', age: 20, extra: true });
// => { name: 'alice', age: 20 }（未知キー extra は除去される）
User.parse({ name: 'alice', age: '20' });
// => throws ZodError（issues: [{ code: 'invalid_type', path: ['age'], ... }]）
```

## Contract

- 成功すると `z.infer<typeof schema>` 型の値を返す。返り値は入力とは別の新しいオブジェクトで、ネストしたオブジェクト・配列も新しく作られる（`Date` などのインスタンスは同じ参照）
- 入力を変更しない。未知キーが除去されるのは返り値の側だけ
- 失敗すると `ZodError`（`Error` のサブクラス、`name: 'ZodError'`）を投げる。`issues` に全項目の失敗が配列でまとまり、最初の 1 件で止まらない。各 issue は `code` / `path` / `message` を持つ
- スキーマに無いキーは既定で除去する。`.strict()`（`z.strictObject`）なら `unrecognized_keys` で失敗、`.passthrough()`（`z.looseObject`）ならそのまま残す
- `null` / `undefined` を渡すと `path: []` の `invalid_type` で失敗する
- `.default(値)` を付けたキーは欠けていれば補われる
- 非同期の `refine` / `transform` を含むスキーマを `parse` すると `ZodError` ではない例外（`$ZodAsyncError`）を投げる。`parseAsync` を使う

## Alternatives

- 例外を投げたくない場合は `safeParse`（カード validation-safe-parse）
- 他ライブラリでは valibot（`v.parse`）、ajv（JSON Schema）。ここでは名前のみ

## Pitfalls

- 未知キーが黙って消えるので、受け取ったデータをそのまま横流しする用途では情報が落ちる。透過させるなら `z.looseObject`
- 型付き変数を渡しても検証は走る。戻り値の型は入力の型ではなくスキーマから決まる
- `ZodError.message` は `issues` の JSON 文字列。人間向けの表示には `z.prettifyError(error)`
- `.transform()` / `.refine()` の中で投げた例外は `ZodError` にならず、そのまま伝播する

## Test

`examples/validation-parse-schema.test.ts`
