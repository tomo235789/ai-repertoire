---
id: number-round-to
lang: typescript
title: 数値を指定した小数桁数で四捨五入する
tags: [四捨五入, 小数桁, 丸め, round, precision, decimal-places, to-fixed]
lib: es-toolkit
fn: round
since: "1.0.0"
verified: 2026-09-17
status: public
---

小数第 n 位（負なら 10 の n 乗の位）で四捨五入した数値を返す。表示用の桁揃えや、集計値の丸めに使う。

## Signature

```ts
function round(value: number, precision?: number): number
```

## Usage

```ts
import { round } from 'es-toolkit';

round(1.2345);     // => 1
round(1.2345, 2);  // => 1.23
round(1250, -2);   // => 1300
round(2.5);        // => 3
```

## Contract

- `Math.round(value * 10 ** precision) / 10 ** precision` を返す。`precision` 省略時は `0`
- `precision` が負なら 10 の位・100 の位で丸める（`round(1234.5678, -2)` は `1200`）
- `.5` は `Math.round` と同じく正の無限大方向に丸める（`round(2.5)` は `3`、`round(-2.5)` は `-2`）。偶数丸めではない
- 浮動小数点の補正はしない。`round(1.005, 2)` は `1.005 * 100` が `100.49999999999999` になるため `1`
- `precision` が整数でないと `Error` を投げる（小数、`NaN`）
- `value` が `NaN` なら `NaN`、`Infinity` なら `Infinity`。`10 ** precision` が `Infinity` や `0` になるほど極端な `precision` では `NaN` になる

## Alternatives

- 桁を揃えた文字列（`'1.50'`）が欲しいなら stdlib の `value.toFixed(2)`
- 補正付きの丸め（`round(1.005, 2)` を `1.01` にしたい）なら `es-toolkit/compat` の `round`（lodash と同じく指数表記を経由して丸める）
- 切り上げ・切り捨てなら `es-toolkit/compat` の `ceil` / `floor`（`precision` 付き）
- 金額など誤差を許容できない値は整数（最小単位）で扱う

## Pitfalls

- lodash の `round(1.005, 2)` は `1.01` だが es-toolkit は `1`。移行時に結果が変わり得る
- Python の `round()` は偶数丸めで `round(2.5)` が `2`、`round(-1.5)` が `-2`。es-toolkit は `3` と `-1`
- `toFixed` とも一致しない。`(1.45).toFixed(1)` は `'1.4'` だが `round(1.45, 1)` は `1.5`
- `round(-0.4)` は `-0` を返す。`Object.is` や `1 / x` で符号を見る処理では注意する

## Test

`examples/number-round-to.test.ts`
