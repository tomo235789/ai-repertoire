---
id: set-difference
lang: typescript
title: 2 つの集合の差集合を作る
tags: [差集合, 集合演算, 除外, 共通部分, difference, set-operations, exclude, subset]
lib: stdlib
fn: Set.prototype.difference
since: "ES2025"
verified: 2026-09-17
preserves_order: true
status: public
---

自分の要素のうち引数に含まれないものだけを持つ新しい `Set` を返す。「追加された ID」「未処理の項目」のような 2 集合の差を求めるときに使う。

## Signature

```ts
// interface Set<T>（lib.esnext.collection.d.ts）
difference<U>(other: ReadonlySetLike<U>): Set<T>
```

## Usage

```ts
const a = new Set([1, 2, 3, 4]);
const b = new Set([2, 4, 5]);
a.difference(b);          // => Set { 1, 3 }（a にあって b に無いもの）
b.difference(a);          // => Set { 5 }
a.symmetricDifference(b); // => Set { 1, 3, 5 }（どちらか一方にだけあるもの）
a.intersection(b);        // => Set { 2, 4 }
new Set([1, 2]).isSubsetOf(a); // => true
a;                        // => Set { 1, 2, 3, 4 }（元の Set は変わらない）
```

## Contract

- 順序を保持する。返り値は `this` の要素のうち `other` に無いものを `this` の順で並べた新しい `Set`
- 即時評価。`this` も `other` も変更しない
- 引数は set-like（`size` が数値、`has(value)` と `keys()` を持つ）であればよい。`Set` のほか `Map`（キーで判定）や自作オブジェクトを渡せる。`this.size <= other.size` なら `other.has` で各要素を判定し、そうでなければ `other.keys()` を走査して削る
- 配列やイテレータは set-like ではないので `TypeError`（`size` が `NaN`）。`new Set(arr)` で包む
- 要素の同一性は SameValueZero。`NaN` 同士は同じ要素、オブジェクトは参照が同じときだけ同じ
- `this` が空、または `other` が `this` の全要素を含むなら空の `Set`。`other` が空なら `this` のコピー
- 返り値は常にプレーンな `Set`。サブクラスのインスタンスにはならない
- `symmetricDifference` は `this` の要素で `other` に無いもの（`this` の順）に続けて `other` の要素で `this` に無いもの（`other.keys()` の順）を並べる。`intersection` は小さい方の集合を走査するため、要素の順序は `this` と `other` のどちらが小さいかで変わる
- `isSubsetOf` / `isSupersetOf` / `isDisjointFrom` は真偽値を返す。空集合は任意の集合の部分集合

## Alternatives

- 配列同士で「`arr1` にあって `arr2` に無い要素」が欲しいなら es-toolkit の `difference(arr1, arr2)`（`arr1` の重複はそのまま残る）
- 依存を増やせず ES2025 も使えないなら `new Set([...a].filter((x) => !b.has(x)))`
- 和集合は `union`（カード set-union）
- 述語や変換関数で同一性を決めたいなら es-toolkit の `differenceBy` / `differenceWith`（配列版）

## Pitfalls

- `a.difference([1])` は `TypeError`。配列は `new Set([1])` にしてから渡す
- `a.difference(b)` と `b.difference(a)` は別物。対称な差が欲しいなら `symmetricDifference`
- `intersection` の並びは入力サイズに依存するので、順序に意味を持たせない
- ES2025 のため古いランタイム（Node 22 未満、古いブラウザ）には無い。`lib` に `ESNext` が必要

## Test

`examples/set-difference.test.ts`
