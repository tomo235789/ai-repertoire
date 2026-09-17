---
id: collection-sort-by
lang: typescript
title: 複数のキーで配列を昇順に並べ替える
tags: [並べ替え, ソート, 整列, 複数キー, sort-by, sortBy, multi-key, stable-sort]
lib: es-toolkit
fn: sortBy
since: "1.47.1"
verified: 2026-09-17
preserves_order: true
status: public
---

プロパティ名またはキー関数の配列を渡し、オブジェクト配列を昇順に並べ替える。第 1 キーが同じときだけ第 2 キーを見る、という複数キーのソートに使う。

## Signature

```ts
function sortBy<T extends object>(arr: readonly T[], criteria: ReadonlyArray<((item: T) => unknown) | keyof T>): T[]
```

## Usage

```ts
import { sortBy } from 'es-toolkit';

const rows = [{ g: 'b', v: 2 }, { g: 'a', v: 9 }, { g: 'b', v: 1 }];
sortBy(rows, ['g', (r) => r.v]);
// => [{ g: 'a', v: 9 }, { g: 'b', v: 1 }, { g: 'b', v: 2 }]
```

## Contract

- 安定ソート。すべてのキーが等しい要素は元の相対順を保つ（`Array.prototype.sort` に委ねる）
- 入力配列を変更しない。返り値は新しい配列（要素は同じ参照）
- `criteria` は左から順に評価し、前のキーが等しいときだけ次のキーで比較する
- 各キーはプロパティ名（`keyof T`）か関数。関数は純粋であること。比較のたびに呼ばれるので、各要素につき 1 回ではない
- 昇順のみ。`null` と `undefined` はこの順で末尾に置かれる
- 値の比較は `<` / `>` による。文字列はコード単位で比較され、ロケールは考慮しない
- 空配列を渡すと `[]` を返す
- `sortBy` 自身は例外を投げないが、キー関数や getter が投げた例外はそのまま呼び出し元へ伝播する

## Alternatives

- 単一キーで比較関数を書けるなら stdlib の `arr.toSorted((a, b) => a.v - b.v)`（ES2023）
- 降順や昇順・降順の混在は `orderBy(arr, criteria, ['asc', 'desc'])`。`sortBy` は `orderBy` の全キー `'asc'` 版
- lodash からの移行は `es-toolkit/compat` の `sortBy`（配列で包まない単一キーや省略記法を渡せる）

## Pitfalls

- 日本語や大文字小文字を自然な順で並べたいなら `Intl.Collator` を使った比較関数を `toSorted` に渡す。`sortBy` はコード単位の比較しかしない
- 数値と文字列が混在すると JS の `<` の暗黙変換に従い、意図しない順になる。先に型を揃える
- `NaN` はどの値とも「等しい」扱いになり、並びが定まらない。事前に除くか置き換える
- lodash の `sortBy(arr, 'k')` のようにキーを裸で渡すのは不可。`['k']` と配列で包む
- Python の `sorted(key=...)` は `reverse=True` で全キーが反転する。キーごとに向きを変えたいなら `orderBy`

## Test

`examples/collection-sort-by.test.ts`
