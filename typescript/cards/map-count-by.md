---
id: map-count-by
lang: typescript
title: キー関数で要素の出現回数を数える
tags: [集計, 件数, 出現回数, ヒストグラム, count-by, countBy, tally, frequency]
lib: es-toolkit
fn: countBy
since: "1.0.0"
verified: 2026-09-17
status: public
---

各要素からキーを取り出し、キーごとの出現回数をオブジェクトにまとめる。カテゴリ別の件数表示やヒストグラム作成に使う。

## Signature

```ts
declare function countBy<T, K extends PropertyKey>(arr: readonly T[], mapper: (item: T, index: number, array: readonly T[]) => K): Record<K, number>;
```

## Usage

```ts
import { countBy } from 'es-toolkit';

countBy(['a', 'b', 'a'], (x) => x);
// => { a: 2, b: 1 }
countBy([1, 2, 3, 4, 5], (n) => (n % 2 === 0 ? 'even' : 'odd'));
// => { odd: 3, even: 2 }
countBy([], (x) => x);
// => {}
```

## Contract

- 即時評価。`mapper` は各要素につきちょうど 1 回、先頭から順に `(item, index, array)` で呼ばれる
- 入力配列を変更しない。返り値は新しいプレーンオブジェクト（`Object.prototype` を継承）
- キーはプロパティ名として文字列化される。`1` と `'1'` は同じキー、`undefined` は `'undefined'`、オブジェクトは `'[object Object]'` にまとまる。`symbol` はそのままキーになる
- 値は出現回数（1 以上の整数）。出現しなかったキーは存在しない
- `toString` や `constructor` など `Object.prototype` にある名前をキーにすると **正しく数えられない**。内部で `(result[key] ?? 0) + 1` としているため継承プロパティを拾い、`toString` なら関数の文字列表現に `1` を連結した文字列が入る
- 空配列を渡すと `{}` を返す
- 例外は投げない

## Alternatives

- 依存を増やせない場合は `Map.groupBy(arr, fn)` の各値の `length`、または `reduce` で `Map<K, number>` を作る
- 件数ではなく要素そのものを束ねたいなら `groupBy`（カード collection-group-by）、キーで 1 要素ずつ引きたいなら `keyBy`（カード map-key-by）
- lodash からの移行は `es-toolkit/compat` の `countBy`（プロパティ名文字列を渡せる。返り値は `null` プロトタイプ）

## Pitfalls

- 返り値はオブジェクトなので、整数風のキー（`'1'`, `'2'`）は `Object.keys` で常に昇順・先頭に並ぶ。出現順が要るなら `Map.groupBy`（カード map-group-to-map）
- 数値・真偽値・`null` をキーにしても文字列になる。`result[1]` は動くが型は `Record<number, number>` のままなので、`Object.keys` で戻すと文字列になる点に注意
- ユーザー入力など任意の文字列をキーにすると `toString` / `constructor` などで数が壊れる。`Map.groupBy` で数えるか、キーに接頭辞を付けて `Object.prototype` の名前と衝突しないようにする
- lodash の `countBy(arr, 'prop')` のようなプロパティ名指定は不可。関数を渡す

## Test

`examples/map-count-by.test.ts`
