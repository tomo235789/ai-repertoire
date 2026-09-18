---
id: iter-take
lang: typescript
title: イテレータの先頭から指定個数だけ取り出す
tags: [先頭, 打ち切り, 個数制限, 無限列, take, limit, head, iterator-helpers]
lib: stdlib
fn: Iterator.prototype.take
since: "ES2025"
verified: 2026-09-17
preserves_order: true
status: public
---

イテレータの先頭 `limit` 個だけを流す新しいイテレータを返す。無限ジェネレータやストリームから必要な分だけ取り出すときに使う。

## Signature

```ts
// interface IteratorObject<T, TReturn, TNext>（lib.esnext.iterator.d.ts）
take(limit: number): IteratorObject<T, undefined, unknown>
```

## Usage

```ts
function* naturals() { let n = 0; while (true) yield n++; }

naturals().take(3).toArray();
// => [0, 1, 2]
naturals().drop(5).take(2).toArray();
// => [5, 6]（drop は先頭 n 個を読み捨てる）
[1, 2].values().take(5).toArray();
// => [1, 2]（元が短ければそこで終わる）
```

## Contract

- 遅延評価。`take` を呼んだ時点では元のイテレータを進めず、`next()` のたびに 1 要素ずつ取り出す。`limit` を超える要素は元から取り出さない（`take(2)` は元を 2 回しか進めない、`take(0)` は 1 回も進めない）
- 順序を保持する。元のイテレータが `limit` より短ければあるだけ返して終わる
- `limit` 個目を返した後の `next()` で終端を返し、そのとき元のイテレータの `return()` を呼ぶ（ジェネレータの `finally` が走る）
- 元のイテレータを消費する。返り値は使い捨てで、消費し切った後にもう一度走査すると空になる
- `limit` は整数に切り捨てられる（`take(2.7)` は 2 個）。`Infinity` は全要素
- `limit` が負数、`NaN`、数値に変換できない値、省略（`undefined`）だと `RangeError` を投げる（`take` を呼んだ時点で）
- `drop(count)` も同じ規則で、先頭 `count` 個を読み捨てて残りを流す。元が短ければ空になる

## Alternatives

- 元が配列なら `arr.slice(0, n)`（即時、配列を返す）
- 条件で打ち切るなら `takeWhile`（カード collection-take-while）。Iterator Helper には `takeWhile` / `dropWhile` は無い
- 先頭 n 個を配列で欲しいだけなら `take(n).toArray()`（カード iter-to-array）
- 変換・絞り込みは `map` / `filter`（カード iter-lazy-map / iter-lazy-filter）と組み合わせる

## Pitfalls

- 負数や `NaN` は空にならず `RangeError`。`Array.prototype.slice` の負数（末尾から数える）とは別物
- `filter` の後ろに置くこと。`take(3).filter(...)` は先頭 3 個から絞るので 3 個未満になる
- 無限ジェネレータに `toArray()` や `for...of` を直接使うと止まらない。必ず `take` を挟む
- `take` で止めても元のジェネレータは `return()` で閉じられる。続きから読みたいなら `take` ではなく `next()` を必要回数呼ぶ

## Test

`examples/iter-take.test.ts`
