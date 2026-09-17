---
id: collection-zip
lang: typescript
title: 複数の配列を要素ごとに組にする
tags: [組み合わせ, ペア化, 転置, zip, pair, tuple, combine]
lib: es-toolkit
fn: zip
since: "1.0.0"
verified: 2026-09-17
preserves_order: true
status: public
---

複数の配列を同じ位置どうしで組にして、タプルの配列を作る。ラベルと値のように別々の配列で持っているデータを並べて扱うときに使う。

## Signature

```ts
function zip<T, U>(arr1: readonly T[], arr2: readonly U[]): Array<[T, U]>
function zip<T>(arr1: readonly T[]): Array<[T]>
function zip<T>(...arrs: Array<readonly T[]>): T[][] // 3・4 配列もタプル型のオーバーロードあり
```

## Usage

```ts
import { zip } from 'es-toolkit';

zip(['a', 'b', 'c'], [1, 2, 3]);
// => [['a', 1], ['b', 2], ['c', 3]]
```

## Contract

- 順序を保持する。i 番目のタプルは各配列の i 番目の要素からなる
- 入力配列を変更しない。返り値の各タプルは新しい配列で、要素は同じ参照
- 返り値の長さは **最も長い** 入力配列に合わせる。短い配列の足りない位置は `undefined` で埋まる
- 引数は可変長。1〜4 個まではタプル型（`[T]`〜`[T, U, V, W]`）、5 個以上は `T[][]` になる
- 引数なし、またはすべて空配列なら `[]` を返す
- 例外は投げない

## Alternatives

- 長さが同じ 2 配列だけなら stdlib で `a.map((x, i) => [x, b[i]] as const)`
- 組にした後に加工するなら `zipWith(a, b, (x, y) => ...)`
- 逆操作（タプルの配列を配列の組に戻す）は `unzip`、キー配列と値配列からオブジェクトを作るなら `zipObject`
- lodash からの移行は `es-toolkit/compat` の `zip`

## Pitfalls

- Python の `zip` は **最も短い** 配列で打ち切るが、es-toolkit（と lodash）は最も長い配列に合わせて `undefined` で埋める。Python の `itertools.zip_longest` に相当する
- 長さが揃わないとタプル型 `[T, U]` に `undefined` が混ざるが、型には現れない。長さが違いうる場合は呼び出し側で検査する
- 5 個以上の配列を渡すと要素型が共通の `T` に潰れ、タプル型にならない

## Test

`examples/collection-zip.test.ts`
