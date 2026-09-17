---
id: number-round-to
lang: csharp
title: 数値を指定した小数桁数で四捨五入する
tags: [四捨五入, 小数桁, 丸め, round, precision, decimal-places, to-fixed]
lib: stdlib
fn: Math.Round
since: "6.0"
verified: 2026-09-17
status: public
---

小数第 n 位で丸めた数値を返す。表示用の桁揃えや、集計値の丸めに使う。**既定は銀行家丸め（偶数丸め）** なので、一般的な四捨五入には `MidpointRounding.AwayFromZero` を明示する。

## Signature

```csharp
public static double Round(double value, int digits, MidpointRounding mode)
```

## Usage

```csharp
using System;

Math.Round(1.2345, 2);                                // => 1.23
Math.Round(2.5);                                      // => 2（偶数丸め）
Math.Round(2.5, MidpointRounding.AwayFromZero);       // => 3（一般的な四捨五入）
Math.Round(1.005, 2, MidpointRounding.AwayFromZero);  // => 1（2 進数では 1.00499...）
Math.Round(1.005m, 2, MidpointRounding.AwayFromZero); // => 1.01（decimal は 10 進のまま丸まる）
```

## Contract

- `mode` 省略時は `MidpointRounding.ToEven`。`.5` ちょうどは偶数側へ丸め、`Math.Round(0.5)` は `0`、`Math.Round(1.5)` は `2`、`Math.Round(2.5)` は `2`、`Math.Round(-2.5)` は `-2`
- `MidpointRounding.AwayFromZero` は `.5` を 0 から遠い方へ丸める（`2.5` → `3`、`-2.5` → `-3`）。`ToZero` / `ToNegativeInfinity` / `ToPositiveInfinity` は中間点に限らず常にその方向へ丸める（`Math.Round(2.7, MidpointRounding.ToZero)` は `2`）
- `digits` は `double` で 0〜15、`decimal` で 0〜28。範囲外は `ArgumentOutOfRangeException`。C# の `Math.Round` は負の桁指定を受け付けない（10 の位で丸めるには割ってから丸めて掛け直す）
- `double` は `value * 10^digits` を丸めてから戻すので、2 進数の表現誤差がそのまま出る。`Math.Round(1.005, 2)` は `1.005 * 100` が `100.49999999999999` になるため `1`（`AwayFromZero` でも `1`）。一方 `Math.Round(2.675, 2)` は積が `267.5` ちょうどになるので `2.68`
- `decimal` は 10 進のまま丸めるので、`Math.Round(1.005m, 2)` は `1.00`（偶数丸め）、`AwayFromZero` なら `1.01`
- 返り値は入力と同じ型。`Math.Round(2.5)` は `double` の `2`。`NaN` は `NaN`、`∞` は `∞` のまま。`Math.Round(-0.4)` は `-0`（符号付き零）
- 未定義の `MidpointRounding` 値を渡すと `ArgumentException`。純粋関数

## Alternatives

- `float` は `MathF.Round`。.NET 7 以降はジェネリック数学の `double.Round(value, digits, mode)` も同じ挙動
- 切り上げ・切り捨てなら `Math.Ceiling` / `Math.Floor`（整数のみ。小数桁なら `digits` 付きの `Math.Round(x, 2, MidpointRounding.ToPositiveInfinity)` など）
- 10 の位で丸めたいなら `Math.Round(x / 10) * 10`（`Math.Round(1234.0 / 10, MidpointRounding.AwayFromZero) * 10` は `1230`）
- 金額など誤差を許容できない値は `decimal` か整数（最小単位）で扱う

## Pitfalls

- TypeScript（es-toolkit の `round`）は `.5` を正の無限大方向に丸める（`round(2.5)` は `3`、`round(-2.5)` は `-2`）。C# の既定は Python の `round()` と同じ偶数丸めで `2` と `-2`。`AwayFromZero` を付けても `-2.5` は `-3` になり es-toolkit とは一致しない
- Python の `round(2.675, 2)` は `2.67` だが C# は `2.68`。どちらも表現誤差の影響を受けるが、丸め方の実装が違うので同じ値でも結果が食い違う。`1.005` のように C# でも意図と違う結果になる値はあり、正確な 10 進丸めが要るなら `decimal` を使う
- Python の `round(1250, -2)`（`1200`、偶数丸め）や es-toolkit の `round(1250, -2)` は負の桁で 100 の位を丸められるが、C# の `Math.Round` に負の `digits` を渡すと `ArgumentOutOfRangeException`。移植するときは割ってから丸めて掛け直す
- `AwayFromZero` を付け忘れると `2.5` が `2` になり、テストで初めて気付く。丸めモードは常に明示する

## Test

`examples/NumberRoundToTests.cs`
