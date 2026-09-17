---
id: number-mean
lang: csharp
title: 数値配列の平均を求める
tags: [平均, 算術平均, 集計, mean, average, avg, statistics]
lib: stdlib
fn: Enumerable.Average
since: "6.0"
verified: 2026-09-17
status: public
---

数値シーケンスの算術平均を返す。計測値やスコアの平均を出すときに使う。

## Signature

```csharp
public static double Average(this IEnumerable<int> source)
```

## Usage

```csharp
using System.Linq;

new[] { 1, 2, 3, 4, 5 }.Average();   // => 3
new[] { 1, 2 }.Average();            // => 1.5（int でも double を返す）
new int?[] { 1, null, 2 }.Average(); // => 1.5（null は無視して 2 件で割る）
new int?[] { }.Average();            // => null
new int[] { }.Average();             // => InvalidOperationException
```

## Contract

- `int` / `long` のシーケンスでも `double` を返す。`float` は `float`、`decimal` は `decimal`
- 空のシーケンスは `InvalidOperationException`（`Sequence contains no elements`）を投げる。`NaN` は返さない
- `int?` などの `Nullable` は `null` を無視して残りの件数で割り、空か全部 `null` なら `null` を返す（例外にならない）
- 入力を変更しない。即時評価で 1 回だけ走査する
- `int` は `long` で合計するので `int.MaxValue` を 2 つ渡しても桁あふれしない。`long` の合計が桁あふれすると `OverflowException`
- 要素に `NaN` があれば `NaN`。`+∞` と `-∞` を両方含むと `NaN`
- 浮動小数点の誤差はそのまま（`new[] { 0.1, 0.2, 0.3 }.Average()` は `0.20000000000000004`）
- `source` が `null` なら `ArgumentNullException`

## Alternatives

- オブジェクトから値を取り出して平均するなら `Average(x => x.Score)`（selector 付きの多重定義）
- 空を `NaN` や既定値にしたいなら `xs.DefaultIfEmpty().Average()`（`0` になる）か、`xs.Length == 0 ? double.NaN : xs.Average()`
- 中央値・分位数は無い。`Order()` してから添字で取る
- 合計は `Sum`（カード number-sum-by）

## Pitfalls

- TypeScript（es-toolkit の `mean`）は空配列で `NaN` を返すが、`Average` は例外。Python の `statistics.fmean` と同じ。空を区別したいなら呼び出し側で先に判定する
- `Nullable` 版は `null` を「件数に数えない」。欠損を 0 として数えたいなら `Average(x => x ?? 0)`
- `int` の平均も `1.5` のように `double` になる。整数に戻すなら `Math.Round`（カード number-round-to）で丸めモードを明示する
- `IEnumerable` を `Sum` と `Average` で 2 回列挙すると 2 回走る。先に `ToList()` する

## Test

`examples/NumberMeanTests.cs`
