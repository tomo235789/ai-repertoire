---
id: iter-lazy-filter
lang: typescript
title: イテレータの要素を遅延で絞り込む
tags: [遅延評価, 絞り込み, フィルタ, イテレータ, lazy, filter, iterator-helpers, predicate]
lib: stdlib
fn: Iterator.prototype.filter
since: "ES2025"
verified: 2026-09-17
preserves_order: true
status: public
---

述語が真を返した要素だけを流す新しいイテレータを返す。要素は取り出されるたびに判定されるので、無限ジェネレータや巨大なストリームにも使える。

## Signature

```ts
// interface IteratorObject<T, TReturn, TNext>（lib.esnext.iterator.d.ts）
filter(predicate: (value: T, index: number) => unknown): IteratorObject<T, undefined, unknown>
```

## Usage

```ts
function* naturals() { let n = 0; while (true) yield n++; }

naturals().filter((n) => n % 3 === 0).take(3).toArray();
// => [0, 3, 6]（無限ジェネレータでも必要な分しか判定されない）
Iterator.from(new Set([1, 2, 3, 4])).filter((x) => x % 2 === 0).toArray();
// => [2, 4]
```

## Contract

- 遅延評価。`filter` を呼んだ時点では述語は 1 回も呼ばれず、`next()` のたびに真を返す要素が見つかるまで元のイテレータを進める
- 順序を保持する。述語は元の順に `(value, index)` で呼ばれ、`index` は元のイテレータ上の位置（`0` 始まり、落とした要素も数える）
- 述語の戻り値は truthy 判定。`0` / `''` / `null` を返した要素は落ちる
- 元のイテレータを 1 回だけ走査する。返り値は使い捨てで、消費し切った後にもう一度走査すると空になる
- 返り値は Iterator Helper オブジェクトで `map` / `take` / `toArray` などをチェーンできる。要素は同じ参照のまま
- 空のイテレータからは空のイテレータが返る。例外は投げない
- 述語が関数でないと `TypeError` を投げる（`filter` を呼んだ時点で）

## Alternatives

- 元が配列で全要素を即時に判定してよいなら `Array.prototype.filter`（結果は配列）
- 型で絞り込むときは述語を型ガード `(v): v is S => ...` にすると、`filter<S extends T>` のオーバーロードで要素型が `S` に狭まる
- 条件が偽になった時点で打ち切りたい（絞り込みではなく先頭区間）なら `takeWhile`（カード collection-take-while）。Iterator Helper には `takeWhile` は無い
- 変換は `map`（カード iter-lazy-map）、先頭 n 個は `take`（カード iter-take）

## Pitfalls

- `Array.prototype.filter` と違い結果は配列ではない。件数や添字が要るなら `toArray()` する
- 全要素が偽の無限ジェネレータに `filter` すると `next()` が返ってこない。無限ソースでは `take` と組み合わせる
- `filter(...).map((x, i) => ...)` の `i` は絞り込み後の連番になる。元の位置が要るなら `filter` の述語側で `index` を使う
- 述語で外部状態を変えると、遅延評価のため実行タイミングが読みにくくなる。純粋関数にする

## Test

`examples/iter-lazy-filter.test.ts`
