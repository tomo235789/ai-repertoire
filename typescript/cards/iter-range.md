---
id: iter-range
lang: typescript
title: 等差数列の配列を作る
tags: [連番, 等差数列, 範囲, 数列生成, range, sequence, arithmetic, numbers]
lib: es-toolkit
fn: range
since: "1.0.0"
verified: 2026-09-17
preserves_order: true
status: public
---

`start` から `end` の手前まで `step` 刻みの数値配列を作る。ループの回数指定やページ番号の生成、テストデータ作成に使う。

## Signature

```ts
declare function range(end: number): number[];
declare function range(start: number, end: number): number[];
declare function range(start: number, end: number, step: number): number[];
```

## Usage

```ts
import { range, rangeRight } from 'es-toolkit';

range(4);           // => [0, 1, 2, 3]
range(1, 4);        // => [1, 2, 3]
range(0, 20, 5);    // => [0, 5, 10, 15]
range(0, -4, -1);   // => [0, -1, -2, -3]
range(5, 1);        // => []（step 1 で届かない）
rangeRight(1, 4);   // => [3, 2, 1]（同じ列を逆順に）
```

## Contract

- 即時評価で新しい配列を返す。`start` 以上 `end` 未満、`step` 刻みの昇順（負の `step` なら降順）
- 引数 1 つなら `range(end)` = `range(0, end)`。`step` 省略は `1`
- `step` が正で `start >= end`、または `step` が負で `start <= end` なら `[]`。`range(0)` や `range(-3)` も `[]`
- 要素数は `ceil((end - start) / step)`。`end` と `start` は小数でもよく、`range(0.5, 3)` は `[0.5, 1.5, 2.5]`、`range(2.5)` は `[0, 1, 2]`
- `step` が `0`、小数、`NaN` だと `Error` を投げる（`step` は非 0 の整数のみ）
- `end` が `NaN` や `Infinity` だと配列長が作れず `RangeError` を投げる
- `rangeRight` は同じ引数で同じ要素を逆順に返す。`rangeRight(0, 20, 5)` は `[15, 10, 5, 0]`

## Alternatives

- 依存を増やせない場合は `Array.from({ length: n }, (_, i) => start + i * step)`
- 無限の連番を遅延で流すならジェネレータ（`function* () { let n = 0; while (true) yield n++; }`）と `take`（カード iter-take）
- lodash からの移行は `es-toolkit/compat` の `range`（`step` に小数を渡せる、`start > end` で自動降順など lodash 互換）

## Pitfalls

- `end` は含まない。`1` から `10` までなら `range(1, 11)`
- Python の `range` と違い遅延ではなく配列を作る。巨大な数を渡すとメモリを使う。`range(Infinity)` は `RangeError`
- 小数の `step` は使えない（`Error`）。`0.1` 刻みなら整数で作ってから `map((i) => i / 10)`
- `range(4, -1)` のように `start > end` で `step` を省略すると `[]`。lodash / `es-toolkit/compat` は自動で降順（`[4, 3, 2, 1, 0]`）になるので挙動が違う。降順は `step` に負数を明示するか `rangeRight`

## Test

`examples/iter-range.test.ts`
