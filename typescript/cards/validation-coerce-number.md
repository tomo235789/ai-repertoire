---
id: validation-coerce-number
lang: typescript
title: 文字列などの入力を数値に変換して検証する
tags: [数値変換, 型変換, クエリ文字列, coerce, number, cast, zod]
lib: zod
fn: z.coerce.number
since: "4.0"
verified: 2026-09-17
status: public
---

クエリ文字列や環境変数のように文字列で届く値を、`Number()` で数値にしてから範囲などを検証する。JSON ボディのように最初から数値で届く値には `z.number()` を使う。

## Signature

```ts
z.coerce.number(params?): ZodCoercedNumber  // .parse(data: unknown): number
```

## Usage

```ts
import { z } from 'zod';

const Port = z.coerce.number().int().min(1).max(65535);
Port.parse('8080');   // => 8080
Port.parse('');       // => throws ZodError（'' → 0 になり min(1) で失敗）
Port.parse('abc');    // => throws ZodError（NaN: invalid_type）
z.coerce.number().parse(null); // => 0（Number(null) は 0）
```

## Contract

- 入力に `Number(input)` を適用してから `z.number()` と同じ検証をする。`'12'` → 12、`' 7 '` → 7、`'1e3'` → 1000、`'0x10'` → 16、`true` → 1、`12n` → 12、`Date` → エポックミリ秒
- `''` / `'  '` / `null` / `false` / `[]` は 0 になって成功する
- `'abc'` / `undefined` / `{}` は `NaN` になり `invalid_type`（message は `received NaN`）で失敗する
- `Infinity` / `'Infinity'` は失敗する（zod 4 の `z.number()` は有限数のみ通す）
- `.int()` / `.min()` / `.max()` などのチェックは変換後の値に対して行う
- `.optional()` を付けると `undefined` はそのまま通る。`.nullable()` を付けると `null` は 0 にならず `null` のまま通る
- `z.number()` は文字列 `'12'` を `invalid_type`（`received string`）で拒否する

## Alternatives

- 空文字や `null` を「未指定」として扱いたい場合は `z.string().trim().min(1).pipe(z.coerce.number())`（`''` は `min(1)` で失敗、`' 12 '` は 12）
- 他ライブラリでは valibot（`v.pipe(v.string(), v.transform(Number))`）。ここでは名前のみ

## Pitfalls

- `''` と `null` が 0 として通るのが最大の罠。「未入力」と「0」を区別する必要があるなら `.min(1)` や上記の `pipe` で塞ぐ
- `Number()` の変換なので `'0x10'` や `'1e3'` も通る。10 進の整数だけを受けたいなら `z.string().regex(/^\d+$/).transform(Number)` のように文字列側で絞る
- `z.infer` の入力側は `unknown`。フォームから来た値をそのまま渡せるが、型で守られているわけではない
- 大きな整数は `Number` の精度（`Number.MAX_SAFE_INTEGER`）で丸められる

## Test

`examples/validation-coerce-number.test.ts`
