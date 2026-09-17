---
id: object-map-values
lang: csharp
title: オブジェクトの各値を変換して同じキーの新しいオブジェクトを作る
tags: [値の変換, 辞書の変換, 辞書のmap, map-values, transform, dictionary, ToDictionary]
lib: stdlib
fn: Enumerable.ToDictionary
since: "6.0"
verified: 2026-09-17
preserves_order: true
status: public
---

キーはそのままに、各値だけを関数で変換した新しい `Dictionary` を作る。`Dictionary<K, X>` を `Dictionary<K, Y>` に変換するときに使う。

## Signature

```csharp
public static Dictionary<TKey,TElement> ToDictionary<TSource,TKey,TElement>(this IEnumerable<TSource> source, Func<TSource,TKey> keySelector, Func<TSource,TElement> elementSelector)
```

## Usage

```csharp
using System.Linq;

var scores = new Dictionary<string, int[]> { ["alice"] = new[] { 80, 90 }, ["bob"] = new[] { 70 } };
var counts = scores.ToDictionary(kv => kv.Key, kv => kv.Value.Length);
// => { ["alice"] = 2, ["bob"] = 1 }
```

## Contract

- 返り値のキーは入力と同じ。元の辞書の列挙順で追加される
- 入力辞書を変更しない。返り値は新しい `Dictionary`。`elementSelector` が返した値がそのまま入る（入力の値を返せば同じ参照）
- 即時評価。返る時点で入力をすべて読み終えている
- `elementSelector` は元の辞書の列挙順に各要素につきちょうど 1 回呼ばれる（途中で例外が出ればそこで止まり、以降の要素には呼ばれない）
- 元の辞書の比較器は引き継がれず、返り値は `EqualityComparer<TKey>.Default`。引き継ぐなら第 4 引数に `d.Comparer` を渡す
- 空の辞書を渡すと空の `Dictionary` を返す
- `source` やセレクタが `null` なら呼び出し時に `ArgumentNullException`。`elementSelector` が投げた例外はそのまま伝播する

## Alternatives

- キーも変えるなら `ToDictionary(kv => g(kv.Key), kv => f(kv.Value))`。キーが衝突すると `ArgumentException`（元より緩い比較器、例えば `StringComparer.OrdinalIgnoreCase` を第 4 引数に渡して `"id"` と `"ID"` が同一視される場合も同じ）
- キーと値の両方を使うなら `ToDictionary(kv => kv.Key, kv => f(kv.Key, kv.Value))`
- リストの各要素を変換するなら `Select(f)`（辞書ではない）

## Pitfalls

- es-toolkit の `mapValues`、Python の `{k: f(v) for k, v in d.items()}` と同じ意味論
- `elementSelector` の中で入力辞書に追加すると `InvalidOperationException`（列挙中の変更）になる。入力を書き換えない
- 比較器を渡さずに作った返り値で大文字小文字を無視した引き当てはできなくなる。`StringComparer` の辞書を変換するときは `d.Comparer` を渡す

## Test

`examples/ObjectMapValuesTests.cs`
