---
id: collection-partition
lang: typescript
title: 条件で配列を 2 つに振り分ける
tags: [振り分け, 二分, 条件分割, partition, split, separate, filter-both]
lib: es-toolkit
fn: partition
since: "1.0.0"
verified: 2026-09-17
preserves_order: true
status: public
---

述語が真になる要素と偽になる要素を、1 回の走査で 2 つの配列に振り分ける。`filter` を 2 回書きたくなったときに使う。

## Signature

```ts
function partition<T, U extends T>(arr: readonly T[], isInTruthy: (value: T, index: number, array: readonly T[]) => value is U): [truthy: U[], falsy: Exclude<T, U>[]]
function partition<T>(arr: readonly T[], isInTruthy: (value: T, index: number, array: readonly T[]) => unknown): [truthy: T[], falsy: T[]]
```

## Usage

```ts
import { partition } from 'es-toolkit';

const [even, odd] = partition([1, 2, 3, 4, 5], (n) => n % 2 === 0);
// even => [2, 4]
// odd  => [1, 3, 5]
```

## Contract

- 順序を保持する。両方の配列とも元の並び順のまま
- 入力配列を変更しない。返り値は新しい配列 2 つの組（要素は同じ参照）
- `isInTruthy` は純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる
- 戻り値は truthy / falsy で判定する（`Array.prototype.filter` と同じ）。`0` や `''` は falsy 側に入る
- 型ガード（`value is U`）を渡すオーバーロードがあり、truthy 側は `U[]`、falsy 側は `Exclude<T, U>[]` に絞り込まれる
- 空配列を渡すと `[[], []]` を返す
- 例外は投げない

## Alternatives

- 依存を増やせない場合は `arr.filter(pred)` と `arr.filter((x) => !pred(x))` の 2 回走査
- 3 つ以上に分けたいなら `groupBy`
- lodash からの移行は `es-toolkit/compat` の `partition`（プロパティ名やオブジェクトの省略記法を渡せる）

## Pitfalls

- 返り値はタプル `[truthy, falsy]`。分割代入で受け取る順を逆にしない
- lodash の `partition(arr, 'active')` のような省略記法は不可。関数を渡す
- Python には組み込みの partition が無く、`itertools` のレシピや 2 回の内包表記で書く。意味論は同じ

## Test

`examples/collection-partition.test.ts`
