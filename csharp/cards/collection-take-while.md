---
id: collection-take-while
lang: csharp
title: 条件を満たす間だけ先頭から要素を取り出す
tags: [先頭抽出, 条件付き取得, 前置部分, take-while, TakeWhile, prefix, until]
lib: stdlib
fn: Enumerable.TakeWhile
since: "6.0"
verified: 2026-09-17
preserves_order: true
status: public
---

先頭から述語が真である間の要素だけを取り出し、最初に偽になった時点で打ち切る。ソート済みの列から閾値までの先頭部分を得るときに使う。

## Signature

```csharp
public static IEnumerable<TSource> TakeWhile<TSource>(this IEnumerable<TSource> source, Func<TSource,bool> predicate)
```

## Usage

```csharp
using System.Linq;

var head = new[] { 1, 2, 3, 1 }.TakeWhile(n => n < 3).ToList();
// => [1, 2]
```

## Contract

- 順序を保持する。返り値は入力の先頭部分（前置部分列）
- 入力を変更しない。返り値の要素は同じ参照
- 遅延評価。取り出した分だけ入力を読み進める
- `predicate` は純粋関数であること。先頭から順に、最初に `false` を返した要素まで呼ばれ、それ以降の要素には呼ばれない
- 最初に `false` になった要素は結果に含まないが、入力からは **読み取られている**
- 添字付きの `TakeWhile((x, i) => ...)` のオーバーロードがある
- すべての要素で `true` なら全要素を返し、先頭で `false` なら空。空のシーケンスを渡すと空を返す
- `source` または `predicate` が `null` なら呼び出し時に `ArgumentNullException` を投げる。`predicate` が投げた例外はそのまま伝播する

## Alternatives

- 先頭の条件を満たす部分を **捨てて** 残りが欲しいなら `SkipWhile`。同じ列に両方を使えば連結が元に戻る
- 先頭から個数で取るなら `Take(n)`、範囲なら .NET 6 の `Take(..n)`
- 位置に関係なく条件を満たす要素を集めるなら `Where`

## Pitfalls

- `Where` ではない。途中で 1 つでも偽があれば、その後に真の要素があっても取り出さない
- 打ち切りの要素まで入力から読み取られるので、1 回しか読めないソース（`IEnumerator` を手で進めているストリームなど）ではその要素が失われる
- es-toolkit の `takeWhile` と同じ意味論だが、C# は遅延評価で返り値は `IEnumerable<T>`。添字や `Count` が要るなら `ToList()` する
- 述語は `bool` を返す必要がある。truthy / falsy の判定ではない

## Test

`examples/CollectionTakeWhileTests.cs`
