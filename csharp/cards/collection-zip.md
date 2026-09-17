---
id: collection-zip
lang: csharp
title: 複数の配列を要素ごとに組にする
tags: [組み合わせ, ペア化, 転置, zip, pair, tuple, combine]
lib: stdlib
fn: Enumerable.Zip
since: "6.0"
verified: 2026-09-17
preserves_order: true
status: public
---

2 つ（または 3 つ）のシーケンスを同じ位置どうしでタプルにする。ラベルと値のように別々の列で持っているデータを並べて扱うときに使う。

## Signature

```csharp
public static IEnumerable<(TFirst First, TSecond Second)> Zip<TFirst,TSecond>(this IEnumerable<TFirst> first, IEnumerable<TSecond> second)
```

## Usage

```csharp
using System.Linq;

var pairs = new[] { "a", "b", "c" }.Zip(new[] { 1, 2, 3 }).ToList();
// => [("a", 1), ("b", 2), ("c", 3)]
foreach (var (name, n) in pairs) Console.WriteLine($"{name}={n}");
```

## Contract

- 順序を保持する。i 番目のタプルは各シーケンスの i 番目の要素からなる
- 入力を変更しない。各タプルは新しい `ValueTuple` で、要素は同じ参照
- 遅延評価。タプル 1 つ分ずつ両方の入力を読み進める
- 長さは **最も短い** 入力に合わせて打ち切る。`first` を先に読んでから `second` を読むので、`second` が短いときは `first` から 1 要素余分に消費されている
- 3 つ目を渡す `Zip(second, third)` は 3 要素タプル `(First, Second, Third)` を返す。`Zip(second, (a, b) => ...)` で組にした結果を直接作れる
- どちらかが空なら空のシーケンスを返す
- 引数が `null` なら呼び出し時に `ArgumentNullException` を投げる

## Alternatives

- 添字と組にするなら `Select((x, i) => (x, i))` か .NET 9 の `Index()`
- 長い方に合わせて足りない側を `default` で埋めるなら MoreLINQ の `ZipLongest`。長さが違えば失敗させたいなら MoreLINQ の `EquiZip`（不一致が判明した時点で `InvalidOperationException`）
- 逆操作（タプルの列を 2 つの列に戻す）は `Select(p => p.First)` と `Select(p => p.Second)`

## Pitfalls

- es-toolkit の `zip` は **最も長い** 配列に合わせて `undefined` で埋めるが、C# の `Zip` は Python と同じく最も短い入力で打ち切る
- 長さの不一致は黙って切り捨てられる。取り違えを検出したいなら `EquiZip` を使う
- タプルの要素名は `First` / `Second`（/ `Third`）。分解して受け取るなら `foreach (var (a, b) in ...)`
- 4 つ以上のシーケンスを一度に組にするオーバーロードは無い。`Zip` を重ねるかタプルを入れ子にする

## Test

`examples/CollectionZipTests.cs`
