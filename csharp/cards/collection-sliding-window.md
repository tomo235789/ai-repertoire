---
id: collection-sliding-window
lang: csharp
title: 配列をスライディングウィンドウで走査する
tags: [スライディングウィンドウ, 移動窓, 連続部分列, sliding-window, window, rolling, moving]
lib: MoreLinq
fn: MoreEnumerable.Window
since: "4.0"
verified: 2026-09-17
preserves_order: true
status: public
---

固定長 `size` の窓を 1 つずつずらしながら部分列を切り出す。移動平均や隣接要素の比較に使う。

## Signature

```csharp
public static IEnumerable<IList<TSource>> Window<TSource>(this IEnumerable<TSource> source, int size)
```

## Usage

```csharp
using MoreLinq;

var windows = new[] { 1, 2, 3, 4, 5 }.Window(3).ToList();
// => [[1, 2, 3], [2, 3, 4], [3, 4, 5]]
```

## Contract

- 順序を保持する。窓は先頭から開始位置を 1 つずつずらして並び、窓の中も元の並び順
- 入力を変更しない。各窓は **別のインスタンス**（実体は配列）で、要素は同じ参照。ある窓を書き換えても他の窓には影響しない
- 遅延評価。入力全体を読み切らずに窓を順に返す（最初の窓を返した時点で読んでいるのは先頭の `size + 1` 要素）
- `size` に満たない末尾の窓は **作られない**。入力長が `size` 未満なら空、ちょうど `size` なら窓 1 つを返す
- 空のシーケンスを渡すと空のシーケンスを返す
- `size` が 1 未満なら **呼び出し時** に `ArgumentOutOfRangeException`、`source` が `null` なら呼び出し時に `ArgumentNullException` を投げる

## Alternatives

- 隣接 2 要素だけなら MoreLINQ の `Pairwise((a, b) => ...)`
- 末尾の短い窓も欲しい（es-toolkit の `partialWindows: true` 相当）なら MoreLINQ の `WindowLeft(size)`。先頭から窓が育つ形なら `WindowRight(size)`
- 重ならない分割は `Chunk(size)`（collection-chunk）
- 依存を増やせない場合のみ配列に対して `Enumerable.Range(0, Math.Max(0, xs.Length - size + 1)).Select(i => xs[i..(i + size)])`

## Pitfalls

- es-toolkit の `windowed` と同じく末尾の短い窓は捨てる。more-itertools の `windowed` は `fillvalue` で埋めるので意味論が違う
- `step` 引数は無い。飛ばしながら取るなら `Window(size).Where((w, i) => i % step == 0)` のように間引く
- 各窓の型は `IList<T>` だが実体は固定長の配列なので `Add` は `NotSupportedException` になる
- `using MoreLinq;` を付けると .NET 9 の `Index()` など同名の拡張メソッドが曖昧になる。衝突したら `Enumerable.Index(xs)` と明示する

## Test

`examples/CollectionSlidingWindowTests.cs`
