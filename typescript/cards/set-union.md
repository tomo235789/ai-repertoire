---
id: set-union
lang: typescript
title: 2 つの集合の和集合を作る
tags: [和集合, 集合演算, 結合, 重複除去, union, set-operations, merge, dedupe]
lib: stdlib
fn: Set.prototype.union
since: "ES2025"
verified: 2026-09-17
preserves_order: true
status: public
---

自分と引数の両方の要素を含む新しい `Set` を返す。タグやユーザー ID の集合を重複なく合わせるときに使う。

## Signature

```ts
// interface Set<T>（lib.esnext.collection.d.ts）
union<U>(other: ReadonlySetLike<U>): Set<T | U>
```

## Usage

```ts
const a = new Set([3, 1, 2]);
const b = new Set([2, 4, 1]);
a.union(b);
// => Set { 3, 1, 2, 4 }（a の要素が先、次に b にしか無い要素）
a;
// => Set { 3, 1, 2 }（元の Set は変わらない）
new Set([1]).union(new Map([[2, 'x']]));
// => Set { 1, 2 }（Map は set-like なのでキーが使われる）
```

## Contract

- 順序を保持する。返り値は `this` の要素をその順で並べ、続けて `other` にしか無い要素を `other.keys()` の順で追加した新しい `Set`
- 即時評価。`this` も `other` も変更しない
- 引数は set-like（`size` が数値、`has(value)` と `keys()` を持つ）であればよい。`Set` のほか `Map`（キーが要素になる）や自作オブジェクトを渡せる。`union` は `other.keys()` だけを使い、`has` は呼ばない
- 配列やイテレータは set-like ではないので `TypeError`（`size` が `NaN`）。`new Set(arr)` で包む
- 要素の同一性は SameValueZero。`NaN` 同士や `+0` と `-0` は同じ要素、オブジェクトは参照が同じときだけ同じ
- 空同士なら空の `Set`。片方が空なら他方のコピー
- 返り値は常にプレーンな `Set`。`Set` のサブクラスで呼んでもサブクラスのインスタンスにはならない
- 引数がオブジェクトでない、`size` が `NaN` / 負数、`has` / `keys` が関数でないと `TypeError` または `RangeError`

## Alternatives

- 配列同士の和集合（重複除去済みの配列）が欲しいなら es-toolkit の `union(arr1, arr2)`（`arr1` 側の重複も除去され、順序は同じ規則）
- 依存を増やせず ES2025 も使えないなら `new Set([...a, ...b])`
- 共通部分は `intersection`、差は `difference` / `symmetricDifference`（カード set-difference）、包含判定は `isSubsetOf` / `isSupersetOf` / `isDisjointFrom`
- 複数の `Set` をまとめるなら `sets.reduce((acc, s) => acc.union(s), new Set())`

## Pitfalls

- `a.union([1, 2])` は `TypeError`。配列は `new Set([1, 2])` にしてから渡す
- 破壊的ではない。`a` に要素を足したいなら `for (const x of b) a.add(x)`
- 順序は `this` が先なので `a.union(b)` と `b.union(a)` は要素は同じでも並びが違う
- ES2025 のため古いランタイム（Node 22 未満、古いブラウザ）には無い。`lib` に `ESNext` が必要

## Test

`examples/set-union.test.ts`
