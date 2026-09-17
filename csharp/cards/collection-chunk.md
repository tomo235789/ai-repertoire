---
id: collection-chunk
lang: csharp
title: 配列を固定長の小配列に分割する
tags: [分割, チャンク, バッチ, chunk, split, batch, slice-by-size]
lib: stdlib
fn: Enumerable.Chunk
since: "6.0"
verified: 2026-09-17
preserves_order: true
status: public
---

シーケンスを `size` 個ずつの配列に切り分ける。API のバッチ送信やページ分割で使う。

## Signature

```csharp
public static IEnumerable<TSource[]> Chunk<TSource>(this IEnumerable<TSource> source, int size)
```

## Usage

```csharp
using System.Linq;

var chunks = new[] { 1, 2, 3, 4, 5 }.Chunk(2).ToList();
// => [[1, 2], [3, 4], [5]]
```

## Contract

- 順序を保持する。各配列の中も元の並び順のまま
- 入力を変更しない。各チャンクは新しい配列で、要素は同じ参照
- 遅延評価。返り値を列挙するとチャンク 1 つ分ずつ入力を読み進め、列挙のたびに入力を読み直す
- 割り切れない場合、最後の配列は `size` 未満になる。切り捨てない
- 空のシーケンスを渡すと空のシーケンスを返す
- `size` が 1 未満なら **呼び出し時** に `ArgumentOutOfRangeException`、`source` が `null` なら呼び出し時に `ArgumentNullException` を投げる（列挙を待たない）

## Alternatives

- .NET 5 以前は MoreLINQ の `Batch(size)`
- 各チャンクを `List<T>` で欲しければ `.Chunk(size).Select(c => c.ToList())`
- 重なる窓が欲しいなら MoreLINQ の `Window`（collection-sliding-window）

## Pitfalls

- 返り値は配列ではなく `IEnumerable<T[]>`。`Count` や添字は使えず、複数回列挙すると入力を毎回読み直す。何度も使うなら `ToList()` で確定させる
- es-toolkit の `chunk` は小数や `NaN` も `Error` にするが、C# は `int` なので不正になりうるのは 0 以下だけ。Python の `itertools.batched` と同じく最後が短くなる
- 文字列を渡すと `char` 単位で分割され、サロゲートペアが分断される（`"𠮷a".Chunk(1)` は 3 チャンク）。文字単位で扱うなら `StringInfo` などで書記素に分けてから渡す

## Test

`examples/CollectionChunkTests.cs`
