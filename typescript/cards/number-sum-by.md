---
id: number-sum-by
lang: typescript
title: 配列の各要素から取り出した数値を合計する
tags: [合計, 集計, 合算, sum, sum-by, total, aggregate]
lib: es-toolkit
fn: sumBy
since: "1.0.0"
verified: 2026-09-17
status: public
---

各要素から数値を取り出して合計する。オブジェクト配列の数量や金額の集計に使う。

## Signature

```ts
function sumBy<T>(items: readonly T[], getValue: (element: T, index: number) => number): number
```

## Usage

```ts
import { sumBy } from 'es-toolkit';

const items = [{ name: 'a', qty: 2 }, { name: 'b', qty: 3 }];
sumBy(items, (item) => item.qty);
// => 5
```

## Contract

- 入力配列を変更しない
- `getValue` は純粋関数であること。各要素につきちょうど 1 回、`(element, index)` の引数で先頭から順に呼ばれる
- 空配列を渡すと `0` を返す（初期値 `0` からの `+=`）
- `getValue` の返り値を数値に変換しない。文字列を返すと `+` が文字列連結になり、`undefined` を返すと `NaN` になる
- 要素のどれかが `NaN` なら結果は `NaN`。浮動小数点の誤差はそのまま（`0.1 + 0.2` は `0.30000000000000004`）
- `sumBy` 自身は例外を投げないが、`getValue` が投げた例外はそのまま呼び出し元へ伝播する

## Alternatives

- 要素がそのまま数値なら `sum(arr)`
- 平均は `meanBy(arr, fn)`、最大・最小の要素は `maxBy` / `minBy`
- 依存を増やせない場合のみ stdlib で `arr.reduce((acc, x) => acc + f(x), 0)`
- lodash からの移行は `es-toolkit/compat` の `sumBy`（プロパティ名文字列を渡せる）

## Pitfalls

- lodash の `sumBy(arr, 'qty')` のようなプロパティ名指定は不可。関数を渡す
- 取り出した値が `undefined`（プロパティ欠損）だと合計が `NaN` になる。`?? 0` で補う
- Python の `sum(x.qty for x in items)` と同じ意味論。空なら `0`
- 金額など誤差を許せない値は整数（最小単位）で合計する

## Test

`examples/number-sum-by.test.ts`
