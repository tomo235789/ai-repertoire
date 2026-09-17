---
id: number-sum-by
lang: csharp
title: 配列の各要素から取り出した数値を合計する
tags: [合計, 集計, 合算, sum, sum-by, total, aggregate]
lib: stdlib
fn: Enumerable.Sum
since: "6.0"
verified: 2026-09-17
status: public
---

各要素から数値を取り出して合計する。オブジェクト配列の数量や金額の集計に使う。

## Signature

```csharp
public static int Sum<TSource>(this IEnumerable<TSource> source, Func<TSource, int> selector)
```

## Usage

```csharp
using System.Linq;

var items = new[] { (Name: "a", Qty: 2), (Name: "b", Qty: 3) };
items.Sum(item => item.Qty);
// => 5
```

## Contract

- 入力を変更しない。即時評価で、呼び出した時点で全要素を走査する
- `selector` は純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる
- 空なら `0` を返す。返り値の型は `selector` の返り値の型（`int` / `long` / `float` / `double` / `decimal` とその `Nullable`）
- `int` / `long` は checked 演算で、桁あふれすると `OverflowException` を投げる。`decimal` も `OverflowException`。`double` / `float` は `∞` になり例外は出ない
- `int?` などの `Nullable` を返す `selector` では `null` を無視して合計し、全部 `null` でも `0`
- `double` に `NaN` があれば結果は `NaN`。補正付き加算ではなく素朴な逐次加算で、`0.1` を 10 回足すと `0.9999999999999999`
- `source` か `selector` が `null` なら `ArgumentNullException`。`selector` が投げた例外はそのまま伝播する

## Alternatives

- 要素がそのまま数値なら `xs.Sum()`
- 平均は `Average`（カード number-mean）、最大・最小の要素は `MaxBy` / `MinBy`（.NET 6）
- 桁あふれを `∞` や `long` で受けたいなら `Sum(x => (long)x.Qty)` のように `selector` で広い型に変換する
- 集計を 1 回の走査で複数まとめたいなら `Aggregate` で自前のタプルを畳み込む

## Pitfalls

- TypeScript（es-toolkit の `sumBy`）は取り出した値が `undefined` なら `NaN` になるが、C# は `int?` の `null` を無視する。欠損を 0 扱いにしたいのか除外したいのか、意味は同じでも「何件で割るか」が変わる `Average` では違いが出る
- Python の `sum` は `int` が任意精度で桁あふれしないが、C# の `int` は `OverflowException`。金額や件数の合計は `long` か `decimal` で取り出す
- Python 3.12 以降の `sum` は `float` を補正付きで加算するが、C# は素朴な加算。最下位ビットで結果が異なり得る
- `IEnumerable` を複数回列挙すると毎回 `selector` が走る。`Sum` と `Average` を続けて呼ぶなら先に `ToList()` する

## Test

`examples/NumberSumByTests.cs`
