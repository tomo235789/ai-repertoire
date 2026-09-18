---
id: validation-brand-type
lang: typescript
title: 文字列や数値に名目型を付けて取り違えを防ぐ
tags: [名目型, ブランド型, ID の取り違え防止, brand, nominal-type, opaque-type, zod]
lib: zod
fn: brand
since: "4.0"
verified: 2026-09-17
status: public
---

`string` のままでは区別できない `UserId` と `OrderId` のような値に、型レベルだけのタグを付ける。実行時には何もせず、検証を通った値だけがその型を名乗れる。

## Signature

```ts
schema.brand<B extends PropertyKey>(value?: B): ZodBranded<typeof schema, B>  // z.infer は T & z.$brand<B>
```

## Usage

```ts
import { z } from 'zod';

const UserId = z.string().min(1).brand<'UserId'>();
type UserId = z.infer<typeof UserId>; // string & z.$brand<'UserId'>

const id = UserId.parse('u_1'); // => 'u_1'（実行時は素の string のまま）
function find(id: UserId) { return id; }
find(id);    // OK
find('u_1'); // コンパイルエラー: string は UserId に代入できない
```

## Contract

- 実行時は何もしない。`parse` は元スキーマ（`z.string().min(1)` など）の検証をそのまま行い、値を変えずに返す（`typeof` は `'string'`、元の文字列と `===`）
- `z.infer` の型は `string & z.$brand<'UserId'>`。素の `string` はこの型に代入できず、逆に `UserId` は `string` として使える（`string` 引数に渡せる）
- ブランド名が違う型同士（`UserId` と `OrderId`）は互いに代入できない
- 型引数の代わりに実引数で `brand('UserId')` と書いても同じ型になる（引数は型推論のためだけで、実行時には使われない）
- 型引数も実引数も省略した `brand()` は元のスキーマをそのまま返し、名目型にならない
- `.brand()` の後にも `.optional()` などのメソッドを続けて呼べる

## Alternatives

- zod を使わないなら `type UserId = string & { readonly __brand: 'UserId' }` のような自前の交差型。ただし検証との結び付きは無い
- 他ライブラリでは valibot（`v.brand`）。ここでは名前のみ

## Pitfalls

- 型引数を書き忘れた `brand()` はエラーにならず、ただの `string` になる。`z.infer` の型を確認する
- ブランド付きの値を作る正規の経路は `parse` / `safeParse`。`'u_1' as UserId` とキャストすれば通るが、検証を素通りする
- 実行時の区別はできない。`typeof` / `instanceof` で `UserId` かどうかは判定できないし、JSON にしても普通の文字列
- 自前の `{ __brand }` 型と zod の `$brand` は別の型なので、混在させると互換性がない

## Test

`examples/validation-brand-type.test.ts`
