---
id: collection-group-by
lang: typescript
title: キー関数で配列をグループ化する
tags: [グループ化, 分類, 集約, group-by, groupBy, categorize, bucket]
lib: es-toolkit
fn: groupBy
since: "1.0.0"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、同じキーの要素を配列にまとめたオブジェクトを作る。カテゴリ別の集計や一覧の見出し分けに使う。

## Signature

```ts
function groupBy<T, K extends PropertyKey>(arr: readonly T[], getKeyFromItem: (item: T, index: number, array: readonly T[]) => K): Record<K, T[]>
```

## Usage

```ts
import { groupBy } from 'es-toolkit';

const items = [{ type: 'a', n: 1 }, { type: 'b', n: 2 }, { type: 'a', n: 3 }];
groupBy(items, (x) => x.type);
// => { a: [{ type: 'a', n: 1 }, { type: 'a', n: 3 }], b: [{ type: 'b', n: 2 }] }
```

## Contract

- 順序を保持する。各グループの配列は元の出現順のまま
- 入力配列を変更しない。返り値は新しいプレーンオブジェクト（`Object.prototype` を継承）で、要素は同じ参照
- `getKeyFromItem` は純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる
- キーはプロパティ名として扱われる。数値キーは文字列化され、`1` と `'1'` は同じグループになる
- `toString` や `constructor` など `Object.prototype` にある名前もキーにできる（`Object.hasOwn` で判定）
- 空配列を渡すと `{}` を返す
- 例外は投げない

## Alternatives

- 依存を増やせない場合は ES2024 の `Object.groupBy(arr, fn)`（返り値は `null` プロトタイプ）
- キーがオブジェクトや、グループの挿入順を保ちたい場合は `Map.groupBy(arr, fn)`
- 件数だけ欲しいなら `countBy`、キーが一意で 1 要素ずつ引きたいなら `keyBy`
- lodash からの移行は `es-toolkit/compat` の `groupBy`（プロパティ名文字列を渡せる）

## Pitfalls

- 返り値はオブジェクトなので、整数風のキー（`'1'`, `'2'`）は `Object.keys` で常に昇順・先頭に並ぶ。出現順でグループを走査したいなら `Map.groupBy` を使う
- lodash の `groupBy(arr, 'type')` のようなプロパティ名指定は不可。関数を渡す
- Python の `itertools.groupby` は **連続する** 要素しかまとめない（事前ソートが必要）。es-toolkit は配列全体をまとめる

## Test

`examples/collection-group-by.test.ts`
