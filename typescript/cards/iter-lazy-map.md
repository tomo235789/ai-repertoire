---
id: iter-lazy-map
lang: typescript
title: イテレータの各要素を遅延で変換する
tags: [遅延評価, 変換, イテレータ, ジェネレータ, lazy, map, iterator-helpers, transform]
lib: stdlib
fn: Iterator.prototype.map
since: "ES2025"
verified: 2026-09-17
preserves_order: true
status: public
---

イテレータの各要素にコールバックを適用した新しいイテレータを返す。要素は取り出されるたびに変換されるので、無限ジェネレータや巨大なストリームにも使える。

## Signature

```ts
// interface IteratorObject<T, TReturn, TNext>（lib.esnext.iterator.d.ts）
map<U>(callbackfn: (value: T, index: number) => U): IteratorObject<U, undefined, unknown>
```

## Usage

```ts
function* naturals() { let n = 0; while (true) yield n++; }

naturals().map((n) => n * n).take(3).toArray();
// => [0, 1, 4]（無限ジェネレータでも先頭 3 個だけ計算される）
Iterator.from([1, 2, 3]).map((x, i) => x * 10 + i).toArray();
// => [10, 21, 32]（配列などの iterable は Iterator.from で包む）
```

## Contract

- 遅延評価。`map` を呼んだ時点ではコールバックは 1 回も呼ばれず、`next()` で要素が取り出されるたびに 1 要素ずつ変換される
- 順序を保持する。コールバックは元の順に `(value, index)` で呼ばれ、`index` は `0` から数える
- 元のイテレータを 1 回だけ走査する。返り値は使い捨てで、`toArray()` や `for...of` で消費し切った後にもう一度走査すると空になる
- 返り値は `Iterator` を継承した Iterator Helper オブジェクトで、`[Symbol.iterator]()` は自分自身を返す。`filter` / `take` / `toArray` などを続けてチェーンできる
- 途中で `break` や `return()` で止めると元のイテレータの `return()` も呼ばれ、ジェネレータの `finally` が走る
- 空のイテレータからは空のイテレータが返る。例外は投げない
- コールバックが関数でないと `TypeError` を投げる（`map` を呼んだ時点で）

## Alternatives

- 元が配列で全要素を即時に変換してよいなら `Array.prototype.map`（第 3 引数に配列を受け取れる、結果は配列）
- 配列以外の iterable（`Set`、`Map`、文字列、ジェネレータ）は `Iterator.from(iterable)` で Iterator Helper にしてから `map` する
- 絞り込みは `filter`（カード iter-lazy-filter）、先頭 n 個は `take`（カード iter-take）、配列にするのは `toArray`（カード iter-to-array）
- 変換後の要素をさらに平坦化するなら `flatMap`（コールバックは iterable / iterator を返す）

## Pitfalls

- `Array.prototype.map` と違い結果は配列ではない。`.length` や添字アクセスはできず、`toArray()` か `Array.from` で配列にする
- 1 回しか走査できない。同じ結果を 2 度使うなら `toArray()` で配列に落としてから使う
- 配列に直接 `.map` するのはただの `Array.prototype.map`（即時評価）。遅延にしたいなら `arr.values().map(...)` か `Iterator.from(arr).map(...)`
- `Iterator.from` は引数が既にネイティブのイテレータならそれ自身を返し、`next()` しか持たないプレーンオブジェクトはラップして Iterator Helper にする

## Test

`examples/iter-lazy-map.test.ts`
