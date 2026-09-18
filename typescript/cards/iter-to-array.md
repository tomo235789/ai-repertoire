---
id: iter-to-array
lang: typescript
title: イテレータを配列に変換する
tags: [配列化, 実体化, 消費, イテレータ, to-array, collect, materialize, iterator-helpers]
lib: stdlib
fn: Iterator.prototype.toArray
since: "ES2025"
verified: 2026-09-17
preserves_order: true
status: public
---

イテレータを最後まで走査し、取り出した要素を配列にして返す。`map` / `filter` / `take` のチェーンの終端で使う。

## Signature

```ts
// interface IteratorObject<T, TReturn, TNext>（lib.esnext.iterator.d.ts）
toArray(): T[]
```

## Usage

```ts
new Map([['a', 1], ['b', 2]]).keys().toArray();
// => ['a', 'b']
[1, 2, 3, 4].values().filter((x) => x % 2 === 0).map((x) => x * 10).toArray();
// => [20, 40]
const it = [1, 2, 3].values();
it.next();
it.toArray();
// => [2, 3]（残りだけ。it はこれで空になる）
```

## Contract

- 即時評価。呼んだ時点でイテレータを終端まで進め、新しい配列を返す
- 順序を保持する。要素は同じ参照のまま入る
- イテレータを消費する。既に `next()` で進めた分は含まれず、`toArray()` の後はイテレータが空になり、再度 `toArray()` すると `[]` を返す
- 終端まで進めるので、ジェネレータなら `finally` が走る（`return` した値は捨てられ、配列に含まれない）
- 空のイテレータには `[]` を返す
- `this` が `next()` を持たないオブジェクト（配列など）だと `TypeError` を投げる

## Alternatives

- 任意の iterable を配列にするなら `Array.from(iterable)` か `[...iterable]`。配列・`Set`・`Map`・文字列にそのまま使える（`toArray` は Iterator Helper のメソッドなので `Iterator.from` で包む必要がある）
- `Array.from` は array-like（`{ length: n }`）も受け取り、第 2 引数で変換関数も渡せる。`toArray` にはどちらも無い
- 無限イテレータは `take(n)`（カード iter-take）で区切ってから `toArray()` する

## Pitfalls

- 無限ジェネレータに直接 `toArray()` すると止まらない
- 配列に対して `[1, 2].toArray()` は無い（`TypeError`）。`[1, 2].values().toArray()` か `Iterator.from([1, 2]).toArray()`
- `Set` や `Map` 自体は Iterator Helper ではないので、`set.toArray()` ではなく `set.values().toArray()`（または `[...set]`）
- チェーンの途中で `toArray()` すると以降は配列操作になり遅延評価の利点が消える。終端で 1 回だけ呼ぶ

## Test

`examples/iter-to-array.test.ts`
