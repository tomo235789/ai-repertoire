---
id: object-deep-merge
lang: typescript
title: 2 つのオブジェクトを再帰的にマージした新しいオブジェクトを作る
tags: [深いマージ, 再帰マージ, 設定の上書き, deep-merge, merge, defaults, override]
lib: es-toolkit
fn: toMerged
since: "1.0.0"
verified: 2026-09-17
status: public
---

ネストしたオブジェクトを再帰的に重ね合わせ、どちらの入力も変更せずに新しいオブジェクトを返す。デフォルト設定にユーザー設定を上書きするときに使う。

## Signature

```ts
function toMerged<T extends Record<PropertyKey, any>, S extends Record<PropertyKey, any>>(target: T, source: S): T & S
```

## Usage

```ts
import { toMerged } from 'es-toolkit';

const defaults = { retry: 3, log: { level: 'info', file: 'app.log' } };
const overrides = { log: { level: 'debug' } };
toMerged(defaults, overrides);
// => { retry: 3, log: { level: 'debug', file: 'app.log' } }
```

## Contract

- `target` も `source` も変更しない。`target` を `cloneDeep` で深くコピーしてからマージする
- プレーンオブジェクト同士・配列同士は再帰的にマージする。配列はインデックスごとに上書きし、`target` 側が長ければ残りは残る（`[1, 2, 3]` と `[9]` は `[9, 2, 3]`）。連結はしない
- `source` 側のプレーンオブジェクト・配列は新しい容器にコピーされ、返り値と `source` は参照を共有しない。それ以外のオブジェクト（`Date`、クラスのインスタンスなど）は `source` の参照がそのまま入る
- `source` の値が `undefined` のキーは `target` の定義済みの値を上書きしない。`null` は上書きする
- 片方だけがプレーンオブジェクト/配列なら再帰せず `source` の値で置き換える
- `source` の自身の列挙可能な文字列キーだけを見る。`__proto__` キーは無視する（プロトタイプ汚染を防ぐ）
- 例外は投げない

## Alternatives

- `target` を破壊的に更新してよいなら `merge(target, source)`（`toMerged` は `merge` の非破壊版。返り値は `target` 自身）
- 衝突時の解決を自分で決めるなら `mergeWith(target, source, (a, b) => ...)`（配列を連結したい場合など。`target` を変更する）
- 1 段階だけでよいなら stdlib の `{ ...a, ...b }`
- lodash からの移行は `es-toolkit/compat` の `merge`（可変長引数。`target` を変更する）

## Pitfalls

- 配列は連結ではなくインデックス単位の上書き。連結したいなら `mergeWith` で `Array.isArray(a) ? a.concat(b) : undefined` を返す
- 返り値の型は `T & S` なので、同じキーで型が異なる（`string` と `number` など）とそのプロパティの型は `never` になる
- Python の `{**a, **b}` や `dict.update` は 1 段階のみで再帰しない
- `source` に入れた `Date` や `Map` は参照が共有される。あとから変更すると返り値にも影響する

## Test

`examples/object-deep-merge.test.ts`
