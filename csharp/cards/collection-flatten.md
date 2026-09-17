---
id: collection-flatten
lang: csharp
title: ネストした配列を指定の深さまで平坦化する
tags: [平坦化, フラット化, ネスト解除, flatten, flat, nested, SelectMany]
lib: stdlib
fn: Enumerable.SelectMany
since: "6.0"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素が返すシーケンスを 1 段だけ開いて 1 つのシーケンスにする。二重の配列やリストのリストを一覧にするときに使う。

## Signature

```csharp
public static IEnumerable<TResult> SelectMany<TSource,TResult>(this IEnumerable<TSource> source, Func<TSource,IEnumerable<TResult>> selector)
```

## Usage

```csharp
using System.Linq;

var nested = new[] { new[] { 1, 2 }, Array.Empty<int>(), new[] { 3 } };
var flat = nested.SelectMany(x => x).ToList();
// => [1, 2, 3]
```

## Contract

- 順序を保持する。外側の並び順に、各内側の並び順で展開する
- 入力を変更しない。返り値の要素は同じ参照（開かれずに残る内側の配列も同じ参照）
- 遅延評価。取り出した分だけ外側・内側を読み進める
- 開くのは 1 段だけ。`selector` が返したシーケンスの要素をそのまま返し、要素がさらに `IEnumerable` でも開かない
- `selector` は純粋関数であること。列挙 1 回あたり各外側要素につきちょうど 1 回呼ばれる。添字付きの `SelectMany((x, i) => ...)`、内側の要素と外側の要素から結果を作る `SelectMany(collectionSelector, resultSelector)` のオーバーロードがある
- 空のシーケンス、または空のシーケンスだけを含むシーケンスを渡すと空を返す
- `source` または `selector` が `null` なら呼び出し時に `ArgumentNullException` を投げる。`selector` が `null` を返すと、その要素に達した時点（列挙時）で `NullReferenceException` になる

## Alternatives

- 決まった数のシーケンスを連結するだけなら `Concat(a, b)`
- 2 段開くなら `SelectMany` を 2 回、深さを問わず開くなら再帰関数を書くか MoreLINQ の `Flatten()`（`object` の列になる。文字列は開かない）
- クエリ構文なら `from inner in nested from x in inner select x`

## Pitfalls

- es-toolkit の `flatten` は `depth` を取るが、`SelectMany` は 1 段固定。深さを変数にしたいなら再帰で書く
- `string` は `IEnumerable<char>` なので `new[] { "ab", "cd" }.SelectMany(s => s)` は文字に分解される（Python と同じ）。文字列を要素のまま残したいなら `SelectMany` を使わない
- 内側が `null` だと列挙時に `NullReferenceException` になる。`selector` で `?? Enumerable.Empty<T>()` を付ける

## Test

`examples/CollectionFlattenTests.cs`
