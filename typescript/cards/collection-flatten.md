---
id: collection-flatten
lang: typescript
title: ネストした配列を指定の深さまで平坦化する
tags: [平坦化, フラット化, ネスト解除, flatten, flat, nested, depth]
lib: es-toolkit
fn: flatten
since: "1.9.0"
verified: 2026-09-17
preserves_order: true
status: public
---

入れ子になった配列を `depth` 段まで展開して 1 つの配列にする。二重配列を一覧にするときや、段数を限定して開きたいときに使う。

## Signature

```ts
function flatten<T, D extends number = 1>(arr: readonly T[], depth?: D): Array<FlatArray<T[], D>>
```

## Usage

```ts
import { flatten } from 'es-toolkit';

flatten([1, [2, [3, [4]]]]);
// => [1, 2, [3, [4]]]
flatten([1, [2, [3, [4]]]], 2);
// => [1, 2, 3, [4]]
```

## Contract

- 順序を保持する。深さ優先で左から順に展開する
- 入力配列を変更しない。返り値は新しい配列で、`depth` より深い位置に残る配列は同じ参照
- `depth` の既定値は `1`。小数は `Math.floor` で切り捨て、`0` 以下なら展開せず浅いコピーを返す
- `Infinity` を渡すとすべての段を展開する（`flattenDeep` と同じ）
- 展開するのは `Array.isArray` が真の要素だけ。文字列や配列風オブジェクトは展開しない
- 疎配列の空きスロットは `undefined` として残る（`Array.prototype.flat` は取り除く）
- 空配列を渡すと `[]` を返す
- 例外は投げない

## Alternatives

- 依存を増やせない場合は ES2019 の `arr.flat(depth)`（空きスロットの扱い以外は同じ）
- 深さを問わず全部開くなら `flattenDeep(arr)`
- 各要素を変換しながら 1 段開くなら `flatMap`
- lodash からの移行は `es-toolkit/compat` の `flatten`（1 段固定）/ `flattenDepth`（`arguments` や `Symbol.isConcatSpreadable` も展開）

## Pitfalls

- lodash の `flatten` は 1 段固定で深さ指定は `flattenDepth`。es-toolkit は `flatten` 自体が `depth` を取る
- `depth` を変数で渡すと返り値の型は `FlatArray<T[], number>` に広がる。型を効かせたいならリテラルで渡す
- Python には配列の平坦化の組み込みが無く、`itertools.chain.from_iterable` は 1 段だけ開く

## Test

`examples/collection-flatten.test.ts`
