---
id: collection-group-by
lang: csharp
title: キー関数で配列をグループ化する
tags: [グループ化, 分類, 集約, group-by, GroupBy, categorize, bucket]
lib: stdlib
fn: Enumerable.GroupBy
since: "6.0"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、同じキーの要素を `IGrouping` にまとめる。カテゴリ別の集計や一覧の見出し分けに使う。

## Signature

```csharp
public static IEnumerable<IGrouping<TKey,TSource>> GroupBy<TSource,TKey>(this IEnumerable<TSource> source, Func<TSource,TKey> keySelector)
```

## Usage

```csharp
using System.Linq;

var items = new[] { (type: "a", n: 1), (type: "b", n: 2), (type: "a", n: 3) };
foreach (var g in items.GroupBy(x => x.type))
    Console.WriteLine($"{g.Key}: {string.Join(",", g.Select(x => x.n))}");
// a: 1,3
// b: 2
```

## Contract

- 順序を保持する。グループはキーの初出順に並び、各グループの中は元の出現順のまま
- 入力を変更しない。返り値は `IGrouping<TKey, TSource>`（`Key` を持つ `IEnumerable<TSource>`）の列で、要素は同じ参照。各グループは何度でも列挙できる
- 遅延評価だが、最初のグループを取り出した時点で入力を **すべて** 読み切る。列挙のたびに再計算する
- `keySelector` は純粋関数であること。列挙 1 回あたり各要素につきちょうど 1 回、先頭から順に呼ばれる
- キーの比較は `EqualityComparer<TKey>.Default`。第 3 引数に `IEqualityComparer<TKey>` を渡せる
- キーが `null` でもよい。`null` キーのグループが 1 つできる
- 空のシーケンスを渡すと空のシーケンスを返す
- `source` または `keySelector` が `null` なら呼び出し時に `ArgumentNullException` を投げる

## Alternatives

- 同じ結果をキーで何度も引くなら `ToLookup(f)`（即時評価。無いキーは空の列を返す）
- `Dictionary<TKey, List<T>>` が欲しいなら `GroupBy(f).ToDictionary(g => g.Key, g => g.ToList())`
- 件数だけなら .NET 9 の `CountBy(f)`、グループごとに集計するなら `GroupBy(keySelector, elementSelector, resultSelector)` のオーバーロード
- 入力を読み切りたくないなら MoreLINQ の `GroupAdjacent`（連続する同じキーだけをまとめる）

## Pitfalls

- es-toolkit の `groupBy` は数値キーを文字列化して `1` と `'1'` を同じグループにするが、C# はキーの型のままなので別のキー
- Python の `itertools.groupby` は **連続する** 要素しかまとめない（事前ソートが必要）。`GroupBy` は入力全体をまとめる
- `GroupBy` の返り値を何度も列挙すると、そのたびに入力を読み直してグループを作り直す。使い回すなら `ToList()` か `ToLookup`

## Test

`examples/CollectionGroupByTests.cs`
