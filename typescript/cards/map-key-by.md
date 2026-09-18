---
id: map-key-by
lang: typescript
title: キー関数で要素をキー引きできる辞書にする
tags: [索引化, 辞書化, ルックアップ, 一意キー, key-by, keyBy, index-by, lookup]
lib: es-toolkit
fn: keyBy
since: "1.0.0"
verified: 2026-09-17
status: public
---

各要素からキーを取り出し、キーから要素を引けるオブジェクトを作る。ID による参照テーブル作成や、配列の `find` を繰り返す処理の置き換えに使う。

## Signature

```ts
declare function keyBy<T, K extends PropertyKey>(arr: readonly T[], getKeyFromItem: (item: T, index: number, array: readonly T[]) => K): Record<K, T>;
```

## Usage

```ts
import { keyBy } from 'es-toolkit';

const users = [{ id: 'u1', name: 'A' }, { id: 'u2', name: 'B' }];
const byId = keyBy(users, (u) => u.id);
// => { u1: { id: 'u1', name: 'A' }, u2: { id: 'u2', name: 'B' } }
byId.u2.name;
// => 'B'
keyBy([{ id: 'x', v: 1 }, { id: 'x', v: 2 }], (x) => x.id);
// => { x: { id: 'x', v: 2 } }（重複キーは最後の要素が残る）
```

## Contract

- 即時評価。`getKeyFromItem` は各要素につきちょうど 1 回、先頭から順に `(item, index, array)` で呼ばれる
- 同じキーが複数回出たら **最後** の要素が残る。先に出た要素は上書きされる
- 入力配列を変更しない。返り値は新しいプレーンオブジェクト（`Object.prototype` を継承）で、値は同じ参照
- キーはプロパティ名として文字列化される。`1` と `'1'` は同じキー、`undefined` は `'undefined'`
- `toString` など `Object.prototype` にある名前もキーにできる（`Object.hasOwn` で判定）
- 空配列を渡すと `{}` を返す
- 例外は投げない

## Alternatives

- 依存を増やせない場合は `new Map(arr.map((x) => [fn(x), x]))`（キーが文字列化されず、挿入順も保つ。重複は同じく最後が残る）
- 同じキーの要素を全部残したいなら `groupBy`（カード collection-group-by）か `Map.groupBy`（カード map-group-to-map）
- 件数だけなら `countBy`（カード map-count-by）
- lodash からの移行は `es-toolkit/compat` の `keyBy`（プロパティ名文字列を渡せる）

## Pitfalls

- 重複キーは黙って上書きされる。**最初** の要素を残したいなら `keyBy([...arr].reverse(), fn)` にするか、`groupBy` で `[0]` を取る
- 型は `Record<K, T>` で全キーが存在する前提になる。存在しないキーで引くと実行時は `undefined` なので、`noUncheckedIndexedAccess` を有効にするか `byId[id] ?? fallback` で受ける
- 返り値はオブジェクトなので整数風のキーは `Object.keys` で昇順・先頭に並ぶ。元の順で走査したいなら `Map` を使う
- lodash の `keyBy(arr, 'id')` のようなプロパティ名指定は不可。関数を渡す

## Test

`examples/map-key-by.test.ts`
