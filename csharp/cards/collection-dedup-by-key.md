---
id: collection-dedup-by-key
lang: csharp
title: キー関数で配列の重複を除去する
tags: [重複除去, ユニーク, 一意化, dedupe, uniq, distinct, unique-by]
lib: stdlib
fn: Enumerable.DistinctBy
since: "6.0"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、キーが同じ要素を 1 つに絞る。ID を持つオブジェクト列の重複除去に使う。

## Signature

```csharp
public static IEnumerable<TSource> DistinctBy<TSource,TKey>(this IEnumerable<TSource> source, Func<TSource,TKey> keySelector)
```

## Usage

```csharp
using System.Linq;

var users = new[] { (id: 1, name: "a"), (id: 2, name: "b"), (id: 1, name: "c") };
var unique = users.DistinctBy(u => u.id).ToList();
// => [(id: 1, name: "a"), (id: 2, name: "b")]
```

## Contract

- 順序を保持する。同じキーの要素は **最初に出現したもの** を残す
- 入力を変更しない。返り値の要素は同じ参照
- 遅延評価。取り出した分だけ入力を読み進め、列挙のたびに入力を読み直す
- `keySelector` は純粋関数であること。列挙 1 回あたり各要素につきちょうど 1 回、先頭から順に呼ばれる
- キーの比較は `EqualityComparer<TKey>.Default`（`Equals` と `GetHashCode`）。第 3 引数に `IEqualityComparer<TKey>` を渡せる（`StringComparer.OrdinalIgnoreCase` など）
- キーが `null` でもよい。`null` キーの要素も 1 つだけ残る
- 空のシーケンスを渡すと空のシーケンスを返す
- `source` または `keySelector` が `null` なら呼び出し時に `ArgumentNullException` を投げる

## Alternatives

- 要素そのものがキーなら `Distinct()`。`record` は値で等しいので `Distinct()` だけで重複を除ける
- 順序を捨ててよければ `ToHashSet()`、キーで引く辞書が欲しいなら `ToDictionary`（キー重複で `ArgumentException`）
- .NET 5 以前は `GroupBy(f).Select(g => g.First())`（最初の要素を取り出す時点で入力を読み切る）

## Pitfalls

- 複合キーはタプル `(u.A, u.B)` か匿名型・`record` で返す。`Equals` を実装しない `class` を返すと参照比較になり何も除去されない
- 大文字小文字や全角半角の違いを同一視したいなら、キーを正規化するか比較器を渡す
- Python の `{key(x): x for x in xs}.values()` は **最後** の要素を残すので意味論が逆
- es-toolkit の `uniqBy` はオブジェクトを参照で比較するが、C# はタプルやレコードなら値で比較される

## Test

`examples/CollectionDedupByKeyTests.cs`
