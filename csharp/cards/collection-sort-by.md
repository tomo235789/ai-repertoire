---
id: collection-sort-by
lang: csharp
title: 複数のキーで配列を昇順に並べ替える
tags: [並べ替え, ソート, 整列, 複数キー, sort-by, OrderBy, multi-key, stable-sort]
lib: stdlib
fn: Enumerable.OrderBy
since: "6.0"
verified: 2026-09-17
preserves_order: true
status: public
---

キー関数で昇順に並べ替え、`ThenBy` を連ねて第 1 キーが同じときだけ第 2 キーを見る複数キーのソートにする。

## Signature

```csharp
public static IOrderedEnumerable<TSource> OrderBy<TSource,TKey>(this IEnumerable<TSource> source, Func<TSource,TKey> keySelector)
```

## Usage

```csharp
using System.Linq;

var rows = new[] { (g: "b", v: 2), (g: "a", v: 9), (g: "b", v: 1) };
var sorted = rows.OrderBy(r => r.g).ThenBy(r => r.v).ToList();
// => [(g: "a", v: 9), (g: "b", v: 1), (g: "b", v: 2)]
```

## Contract

- 安定ソート。キーが等しい要素は元の相対順を保つ（`OrderByDescending` / `ThenByDescending` でも保つ）
- 入力を変更しない。返り値の要素は同じ参照
- 遅延評価だが、最初の要素を取り出した時点で入力を **すべて** 読み切って並べ替える。列挙のたびに再計算する
- `keySelector` は純粋関数であること。列挙 1 回あたり各要素につきちょうど 1 回呼ばれる（比較のたびではない）
- 複数キーは `ThenBy` / `ThenByDescending` を連ねる。前のキーが等しいときだけ次のキーで比較する。`OrderBy` を 2 回連ねると **後の `OrderBy` だけ** が効く
- 比較は `Comparer<TKey>.Default`。`null` は最小として先頭（降順なら末尾）に置かれる。第 3 引数に `IComparer<TKey>` を渡せる
- 空のシーケンスを渡すと空のシーケンスを返す
- `source` または `keySelector` が `null` なら呼び出し時に `ArgumentNullException`。`IComparable` を実装しない型のキーは、列挙時に `null` でないキー同士を比較した時点で `InvalidOperationException`（`InnerException` は `ArgumentException`）を投げる。要素が 1 つだけ、または `null` との比較だけなら投げない

## Alternatives

- 要素そのものがキーなら .NET 7 の `Order()` / `OrderDescending()`
- その場で並べ替えてよければ `List<T>.Sort` / `Array.Sort`（返り値なし。**安定性を保証しない** ので、キーが等しい要素の順は保証されない）
- 最小・最大の 1 件だけなら `MinBy` / `MaxBy`（.NET 6）

## Pitfalls

- `List<T>.Sort` は要素数が少ないと偶然安定に見えることがあるが、同じキーの要素の順が保たれる保証は無い。安定性が要るなら `OrderBy`
- `string` キーの `Comparer<string>.Default` は現在のカルチャの比較で、`a, A, b, B` のように大小を混ぜて並ぶ。序数で並べるなら `StringComparer.Ordinal` を渡す
- `double.NaN` は最小として先頭に置かれる（比較結果が定まらない JS / Python とは違う）
- es-toolkit の `sortBy` は `null` を末尾に置くが、C# は先頭。末尾にするなら `OrderBy(x => x.k is null).ThenBy(x => x.k)` のように振り分ける
- Python の `reverse=True` は全キーをまとめて反転するが、C# はキーごとに `ThenBy` / `ThenByDescending` で向きを変える

## Test

`examples/CollectionSortByTests.cs`
