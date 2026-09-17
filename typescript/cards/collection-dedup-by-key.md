---
id: collection-dedup-by-key
lang: typescript
title: キー関数で配列の重複を除去する
tags: [重複除去, ユニーク, 一意化, dedupe, uniq, distinct, unique-by]
lib: es-toolkit
fn: uniqBy
since: "1.0.0"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、キーが同じ要素を 1 つに絞る。ID を持つオブジェクト配列の重複除去に使う。

## Signature

```ts
function uniqBy<T, U>(arr: readonly T[], mapper: (item: T, index: number, array: readonly T[]) => U): T[]
```

## Usage

```ts
import { uniqBy } from 'es-toolkit';

const users = [{ id: 1, name: 'a' }, { id: 2, name: 'b' }, { id: 1, name: 'c' }];
uniqBy(users, (u) => u.id);
// => [{ id: 1, name: 'a' }, { id: 2, name: 'b' }]
```

## Contract

- 順序を保持する。同じキーの要素は **最初に出現したもの** を残す
- 入力配列を変更しない。返り値は新しい配列（要素は同じ参照）
- `mapper` は純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる
- キーの比較は `Map` と同じ SameValueZero。`NaN` 同士は等しく、オブジェクトは参照で比較される
- 空配列を渡すと `[]` を返す

## Alternatives

- 要素そのものがキーなら `uniq(arr)`（プリミティブ配列は `[...new Set(arr)]` でも同じ）
- 「等しいか」を 2 要素の比較関数で決めたいなら `uniqWith(arr, (a, b) => ...)`
- lodash からの移行は `es-toolkit/compat` の `uniqBy`（プロパティ名文字列を渡せる）

## Pitfalls

- `mapper` が新しいオブジェクトや配列を返すと毎回別キー扱いになり何も除去されない。複合キーは各値が文字列・真偽値・有限の数値に限られるなら `JSON.stringify([a, b])` で文字列へ正規化する（`${a}:${b}` は値に区切り文字が含まれると衝突する）。`null` / `undefined` / `NaN` / `Infinity` はすべて `null` になり区別できないので、区別が必要なら `uniqWith` で比較関数を書く
- lodash の `uniqBy(arr, 'id')` のようなプロパティ名指定は不可。関数を渡す
- Python の `{key(x): x for x in xs}.values()` は **最後** の要素を残すので意味論が逆

## Test

`examples/collection-dedup-by-key.test.ts`
