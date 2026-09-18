---
id: error-invariant
lang: typescript
title: 前提条件を検査して型を絞り込む
tags: [前提条件, 不変条件, 表明, アサーション, 型の絞り込み, invariant, assert, asserts-condition]
lib: es-toolkit
fn: invariant
since: "1.38.0"
verified: 2026-09-17
status: public
---

条件が偽なら `Error` を投げ、真なら以降のコードで条件が成り立つものとして型を絞り込む。「ここには来ないはず」の前提を明示するために使う。

## Signature

```ts
function invariant(condition: unknown, message: string): asserts condition
function invariant(condition: unknown, error: Error): asserts condition
```

## Usage

```ts
import { invariant } from 'es-toolkit';

const user: { id: number; email?: string } | undefined = users.get(id);
invariant(user, `user ${id} not found`);       // 偽なら Error('user 1 not found')
user.id;                                       // => user は undefined でない型に絞り込まれている
invariant(user.email, new TypeError('email is required'));
user.email.toLowerCase();                      // => string に絞り込まれている
invariant(items.length > 0, 'items must not be empty'); // 真なら何もしない（undefined を返す）
```

## Contract

- `condition` が truthy なら何もしない。falsy（`false` / `0` / `''` / `null` / `undefined` / `NaN`）なら第 2 引数に応じて投げる
- 第 2 引数が文字列なら `new Error(message)` を投げる（`name` は `'Error'`）。`Error` のインスタンスならそのオブジェクトを **そのまま** 投げるので、独自クラスや `cause` 付きを使える
- 戻り値の型は `asserts condition`。呼び出し後のコードで `condition` に使った式が真として扱われ、`x !== undefined` や `typeof x === 'string'` の絞り込みが効く
- 絞り込みが効くのは `condition` に渡した式が変数の判定である場合。`invariant(user, ...)` は `user` を truthy な型に、`invariant(user.email, ...)` は `user.email` を `string` に絞る
- `asserts` 関数は **明示的に型注釈した変数か import した関数** として呼ぶ必要がある。`const check = invariant` でも import 元の型が付くので使える

## Alternatives

- Node なら `node:assert` の `assert(value, message)` / `assert.ok`（投げるのは `AssertionError`、`asserts value` 型付き）
- 検証エラーを **値として** 扱いたいならカード result-try-to-result（`attempt`）や zod の `safeParse`
- 開発時だけ検査したいなら `if (import.meta.env.DEV) invariant(...)` のように呼び出し側で囲む（`invariant` 自体は本番でも動く）

## Pitfalls

- `0` や `''` が正当な値の変数に `invariant(value, ...)` を使うと弾いてしまう。`invariant(value !== undefined, ...)` と明示する
- 第 2 引数を省略するとコンパイルは通らないが、`any` 経由で `undefined` が渡ると **`undefined` が throw** される。メッセージは必ず付ける
- メッセージを文字列で渡すと毎回 `Error` が作られるので、ホットパスで `invariant` を多用すると `stack` の生成コストがかかる
- `invariant` は入力検証（ユーザーからの値）には向かない。あくまで「プログラムの前提」用で、入力にはスキーマ検証を使う
- 投げられる `Error` は `stack` の先頭が `invariant` 内部になる。呼び出し位置は 2 行目以降で確認する

## Test

`examples/error-invariant.test.ts`
