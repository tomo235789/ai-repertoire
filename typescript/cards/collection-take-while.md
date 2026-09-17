---
id: collection-take-while
lang: typescript
title: 条件を満たす間だけ先頭から要素を取り出す
tags: [先頭抽出, 条件付き取得, 前置部分, take-while, takeWhile, prefix, until]
lib: es-toolkit
fn: takeWhile
since: "1.0.0"
verified: 2026-09-17
preserves_order: true
status: public
---

先頭から述語が真である間の要素だけを取り出し、最初に偽になった時点で打ち切る。ソート済み配列から閾値までの先頭部分を得るときに使う。

## Signature

```ts
function takeWhile<T>(arr: readonly T[], shouldContinueTaking: (element: T, index: number, array: readonly T[]) => boolean): T[]
```

## Usage

```ts
import { takeWhile } from 'es-toolkit';

takeWhile([1, 2, 3, 1], (n) => n < 3);
// => [1, 2]
```

## Contract

- 順序を保持する。返り値は元配列の先頭部分（前置部分列）
- 入力配列を変更しない。返り値は新しい配列（要素は同じ参照）
- `shouldContinueTaking` は純粋関数であること。先頭から順に、最初に偽を返した要素まで呼ばれ、それ以降の要素には呼ばれない
- 戻り値は truthy / falsy で判定する。最初に偽になった要素は結果に含まない
- すべての要素で真なら元配列の浅いコピー、先頭で偽なら `[]` を返す
- 空配列を渡すと `[]` を返す
- `takeWhile` 自身は例外を投げないが、述語が投げた例外はそのまま呼び出し元へ伝播する

## Alternatives

- 依存を増やせない場合は stdlib で `const end = arr.findIndex((x) => !pred(x)); arr.slice(0, end === -1 ? arr.length : end)`（全要素が真のとき `findIndex` は `-1` を返すので、そのまま `slice` に渡すと末尾 1 要素が欠ける）
- 先頭の条件を満たす部分を **捨てて** 残りが欲しいなら `dropWhile`。`takeWhile` と `dropWhile` の結果を連結すると元配列に戻る
- 末尾から取るなら `takeRightWhile`
- 条件を満たす要素を位置に関係なく集めるなら `filter`
- lodash からの移行は `es-toolkit/compat` の `takeWhile`（省略記法を渡せる）

## Pitfalls

- `filter` ではない。途中で 1 つでも偽があれば、その後に真の要素があっても取り出さない
- 型上は `boolean` を返す述語を要求するが、実装は truthy 判定。`0` や `''` を返すと打ち切られる
- Python の `itertools.takewhile` と同じ意味論（ただし Python は遅延評価）
- lodash の `takeWhile(arr, 'active')` のような省略記法は不可。関数を渡す

## Test

`examples/collection-take-while.test.ts`
