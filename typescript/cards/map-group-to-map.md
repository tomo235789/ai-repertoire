---
id: map-group-to-map
lang: typescript
title: キー関数で要素をグループ化して Map にする
tags: [グループ化, 分類, 挿入順, マップ, group-by, groupBy, bucket, categorize]
lib: stdlib
fn: Map.groupBy
since: "ES2024"
verified: 2026-09-17
preserves_order: true
status: public
---

iterable の各要素からキーを取り出し、同じキーの要素を配列にまとめた `Map` を作る。キーにオブジェクトや数値をそのまま使いたいときや、グループの出現順を保ちたいときに使う。

## Signature

```ts
// interface MapConstructor（lib.es2024.collection.d.ts）
groupBy<K, T>(items: Iterable<T>, keySelector: (item: T, index: number) => K): Map<K, T[]>
```

## Usage

```ts
const items = [{ type: 'b', n: 1 }, { type: 'a', n: 2 }, { type: 'b', n: 3 }];
const groups = Map.groupBy(items, (x) => x.type);
// => Map { 'b' => [{ type: 'b', n: 1 }, { type: 'b', n: 3 }], 'a' => [{ type: 'a', n: 2 }] }
[...groups.keys()];
// => ['b', 'a']（キーが最初に現れた順）
Map.groupBy([1, 2, 3, 4], (x) => x % 2 === 0);
// => Map { false => [1, 3], true => [2, 4] }（キーは文字列化されない）
```

## Contract

- 順序を保持する。`Map` のキーはそのキーが最初に現れた順、各グループの配列は元の出現順
- 即時評価。`keySelector` は各要素につきちょうど 1 回、先頭から順に `(item, index)` で呼ばれる
- 入力を変更しない。返り値は新しい `Map`（`Map.prototype` を継承）で、要素は同じ参照
- キーは任意の値。同一性は `Map` と同じ SameValueZero で、`1` と `'1'` は別グループ、`NaN` 同士は同じグループ、オブジェクトは参照が同じときだけ同じグループ。`undefined` もキーにできる
- 配列以外の iterable（`Set`、`Map`、文字列、ジェネレータ）も受け取れる。array-like（`{ length }`）は `TypeError`
- 空の iterable には空の `Map` を返す
- 第 1 引数が `null` / `undefined`、第 2 引数が関数でないと `TypeError`

## Alternatives

- キーが文字列で結果をオブジェクトとして扱いたいなら `Object.groupBy(items, fn)`（ES2024、`null` プロトタイプのオブジェクト。キーは文字列化される）
- 配列専用で `Object.prototype` を継承したプレーンオブジェクトが欲しいなら es-toolkit の `groupBy`（カード collection-group-by。コールバックに配列も渡る）
- 件数だけ欲しいなら `countBy`（カード map-count-by）、キーが一意で 1 要素ずつ引きたいなら `keyBy`（カード map-key-by）

## Pitfalls

- `Object.groupBy` / es-toolkit `groupBy` はキーをプロパティ名に文字列化するため `1` と `'1'` が同じグループになり、整数風キーが `Object.keys` で昇順先頭に並ぶ。`Map.groupBy` はどちらも起こらない
- オブジェクトをキーにすると参照比較になる。内容が同じ別オブジェクトは別グループ。値で束ねたいなら `JSON.stringify` などで文字列キーにする
- 引数の順序は `(items, keySelector)` で、`items.groupBy(fn)` のようなメソッドではない
- ES2024 のため古いランタイム（Node 20 以前、古いブラウザ）には無い。`lib` に `ES2024` 以上（または `ESNext`）が必要

## Test

`examples/map-group-to-map.test.ts`
