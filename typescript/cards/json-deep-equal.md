---
id: json-deep-equal
lang: typescript
title: 2 つの値が構造的に等しいか比較する
tags: [深い比較, 構造比較, 等価判定, deep-equal, isEqual, compare, structural]
lib: es-toolkit
fn: isEqual
since: "1.0.0"
verified: 2026-09-17
status: public
---

ネストしたオブジェクト・配列・`Date`・`Map`・`Set` などを、参照ではなく中身で比較する。設定の変更検知やメモ化のキー比較に使う。

## Signature

```ts
function isEqual(a: any, b: any): boolean
```

## Usage

```ts
import { isEqual } from 'es-toolkit';

isEqual({ a: 1, b: [1, { c: 2 }] }, { b: [1, { c: 2 }], a: 1 }); // => true（キーの順序は無関係）
isEqual(new Date(0), new Date(0));                                // => true
isEqual(new Map([[1, { a: 1 }]]), new Map([[1, { a: 1 }]]));      // => true
isEqual(Number.NaN, Number.NaN);                                  // => true
isEqual({ a: undefined }, {});                                    // => false
```

## Contract

- プリミティブは `NaN` 同士を `true`、`0` と `-0` を `true` とする。型が違えば `false`（`'1'` と `1`、`null` と `undefined`）
- `Date` は時刻値で比較する（Invalid Date 同士は `true`）。`RegExp` はソースとフラグで比較し、`lastIndex` は見ない
- `Map` は挿入順を問わずキーと値を、`Set` は要素を（要素がオブジェクトでも中身で）比較する
- TypedArray は要素値と型の両方を見る（`Uint8Array` と `Int8Array` は同じ値でも `false`）。`ArrayBuffer` は内容で比較する
- `Error` は `name` と `message` で比較する（`Error('a')` と `TypeError('a')` は `false`）
- 配列とオブジェクト（`[1]` と `{ 0: 1 }`）は `false`。配列は順序も見る
- プロトタイプが違えば `false`。別クラスのインスタンス同士や、クラスインスタンスとプレーンオブジェクトは等しくならない
- `undefined` を値に持つキーと、キーが無い状態は区別する（`{ a: undefined }` と `{}` は `false`）
- 列挙可能な自身のプロパティだけを見る（列挙不可のプロパティは無視）。symbol キーも比較する
- 関数は同じ参照のときだけ `true`
- 循環参照を含む値でも無限ループにならず、構造が同じなら `true`、違えば `false` を返す

## Alternatives

- 参照の同一性だけでよければ `===`
- 順序が固定された素朴な JSON なら `JSON.stringify(a) === JSON.stringify(b)` でも動くが、キー順・`Date`・`Map`・`undefined` で誤判定する
- lodash からの移行は `es-toolkit/compat` の `isEqual`

## Pitfalls

- vitest の `toEqual` は `{ a: undefined }` と `{}` を等しいとみなすが、`isEqual` は区別する。テストの感覚で使うと結果が違う
- クラスインスタンスをプレーンオブジェクトと比べると `false`。API レスポンスと比較するならプレーンオブジェクトに揃えてから
- 大きな構造を毎回比較すると重い。React の再レンダー抑止のような高頻度の場面では、比較する範囲を絞る

## Test

`examples/json-deep-equal.test.ts`
