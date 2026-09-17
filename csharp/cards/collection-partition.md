---
id: collection-partition
lang: csharp
title: 条件で配列を 2 つに振り分ける
tags: [振り分け, 二分, 条件分割, partition, split, separate, filter-both]
lib: stdlib
fn: Enumerable.ToLookup
since: "6.0"
verified: 2026-09-17
preserves_order: true
status: public
---

述語の結果（`bool`）をキーに `ILookup` を作り、`lookup[true]` と `lookup[false]` で 1 回の走査で 2 つに振り分ける。`Where` を 2 回書きたくなったときに使う。

## Signature

```csharp
public static ILookup<TKey,TSource> ToLookup<TSource,TKey>(this IEnumerable<TSource> source, Func<TSource,TKey> keySelector)
```

## Usage

```csharp
using System.Linq;

var lookup = new[] { 1, 2, 3, 4, 5 }.ToLookup(n => n % 2 == 0);
var even = lookup[true].ToList();  // => [2, 4]
var odd = lookup[false].ToList();  // => [1, 3, 5]
```

## Contract

- 順序を保持する。両方とも元の並び順のまま
- 入力を変更しない。返り値の要素は同じ参照
- 即時評価。返る時点で入力をすべて読み終えている。`ILookup` は読み取り専用で、後から入力を変えても反映されない
- 述語は純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる
- `lookup[true]` / `lookup[false]` は該当する要素が無くても例外にならず、空の列を返す。`lookup.Count` はキーの数（0〜2）、`lookup.Contains(true)` で存在を判定できる
- 空のシーケンスを渡すと両方とも空
- `source` または述語が `null` なら呼び出し時に `ArgumentNullException` を投げる

## Alternatives

- MoreLINQ の `Partition(pred)` は `(IEnumerable<T> True, IEnumerable<T> False)` のタプルを返し、`var (even, odd) = xs.Partition(pred)` と分割代入できる（即時評価。`True` が先）
- 2 回走査してよければ `xs.Where(pred)` と `xs.Where(x => !pred(x))`（述語が各要素に 2 回呼ばれる）
- 3 つ以上に分けるなら `GroupBy`（collection-group-by）

## Pitfalls

- es-toolkit の `partition` は `[truthy, falsy]`、more-itertools は `(falsy, truthy)` と順序が逆だが、`ToLookup` はキーで引くので取り違えが起きない
- 述語は `bool` を返す必要がある。truthy / falsy の判定ではない
- `lookup[true]` は `IEnumerable<T>` なので、添字や `Count` プロパティが要るなら `ToList()` する
- 片方しか使わないなら `Where` で十分。`ToLookup` は入力全体をメモリに持つ

## Test

`examples/CollectionPartitionTests.cs`
