---
id: object-map-values
lang: typescript
title: オブジェクトの各値を変換して同じキーの新しいオブジェクトを作る
tags: [値の変換, 辞書の変換, オブジェクトのmap, map-values, transform, dictionary, record]
lib: es-toolkit
fn: mapValues
since: "1.0.0"
verified: 2026-09-17
preserves_order: true
status: public
---

キーはそのままに、各値だけを関数で変換した新しいオブジェクトを作る。`Record<string, X>` を `Record<string, Y>` に変換するときに使う。

## Signature

```ts
function mapValues<T extends object, K extends keyof T, V>(object: T, getNewValue: (value: T[K], key: K, object: T) => V): Record<K, V>
```

## Usage

```ts
import { mapValues } from 'es-toolkit';

const scores = { alice: [80, 90], bob: [70] };
mapValues(scores, (list) => list.length);
// => { alice: 2, bob: 1 }
```

## Contract

- キーの順序を保持する。返り値のキーは入力の自身の列挙可能な文字列キー（`Object.keys`）と同じ。継承したプロパティとシンボルキーは含まれない
- 入力オブジェクトを変更しない。返り値は新しいオブジェクト。コールバックが返した値がそのまま入る（入力の値を返せば同じ参照）
- `getNewValue` は純粋関数であること。各キーにつきちょうど 1 回、`(value, key, object)` の引数で `Object.keys` の順に呼ばれる
- 空オブジェクトを渡すと `{}` を返す
- 例外は投げない（コールバックが投げた例外はそのまま伝播する）

## Alternatives

- キーを変えるなら `mapKeys(obj, (value, key) => ...)`
- キーと値を同時に変えるなら stdlib の `Object.fromEntries(Object.entries(obj).map(([k, v]) => [k2, v2]))`
- コールバックが Promise を返すなら `mapValuesAsync`
- lodash からの移行は `es-toolkit/compat` の `mapValues`（プロパティ名文字列を渡せる）

## Pitfalls

- 自身のキー `'__proto__'` は返り値に自身のプロパティとして残らない（コールバックの返り値がオブジェクトや `null` なら返り値のプロトタイプが変わる）

- 配列を渡すと配列ではなく、インデックス文字列をキーにしたオブジェクトが返る。配列は `Array.prototype.map` を使う
- lodash の `mapValues(obj, 'name')` のようなプロパティ名指定は不可。関数を渡す
- 返り値の型は `Record<K, V>` で、キーごとに異なる値の型は表現できない（すべて `V` に統一される）
- Python の `{k: f(v) for k, v in d.items()}` と同じ意味論

## Test

`examples/object-map-values.test.ts`
