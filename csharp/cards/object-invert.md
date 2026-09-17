---
id: object-invert
lang: csharp
title: オブジェクトのキーと値を入れ替える
tags: [逆引き, キーと値の交換, 逆マッピング, invert, reverse-map, swap-keys, lookup]
lib: stdlib
fn: Enumerable.ToDictionary
since: "6.0"
verified: 2026-09-17
status: public
---

キーと値を入れ替えた新しい `Dictionary` を作る。コード → 名前の対応表から名前 → コードの逆引き表を作るときに使う。

## Signature

```csharp
public static Dictionary<TKey,TElement> ToDictionary<TSource,TKey,TElement>(this IEnumerable<TSource> source, Func<TSource,TKey> keySelector, Func<TSource,TElement> elementSelector)
```

## Usage

```csharp
using System.Linq;

var codeToName = new Dictionary<int, string> { [1] = "red", [2] = "blue" };
var nameToCode = codeToName.ToDictionary(kv => kv.Value, kv => kv.Key);
// => { ["red"] = 1, ["blue"] = 2 }
```

## Contract

- 入力辞書を変更しない。返り値は新しい `Dictionary`
- 返り値のキーは元の値、返り値の値は元のキー。型はそのまま（文字列化しない）
- 即時評価。元の辞書の列挙順で追加される
- 値が重複していると **`ArgumentException`** を投げる（最初の重複に達した時点で失敗し、部分的な結果は返らない）
- 値に `null` があると `ArgumentNullException` を投げる（`null` はキーにできない）
- キーの比較は `EqualityComparer<TValue>.Default`。第 3 引数に `IEqualityComparer` を渡せる
- 空の辞書を渡すと空の `Dictionary` を返す
- `source` が `null` なら呼び出し時に `ArgumentNullException` を投げる

## Alternatives

- 重複する値をまとめたい（`red → [1, 3]`）なら `ToLookup(kv => kv.Value, kv => kv.Key)`
- 重複時に最後を残したい（es-toolkit / Python と同じ挙動）なら `foreach` で `result[kv.Value] = kv.Key` と上書きする。最初を残すなら `DistinctBy(kv => kv.Value)` を先に挟む
- 値がクラスなら `Equals` / `GetHashCode` を実装するか、`record` にしてから逆引き表を作る

## Pitfalls

- es-toolkit の `invert` と Python の `{v: k for k, v in d.items()}` は重複した値で **最後** が黙って残るが、C# の `ToDictionary` は例外になる。重複を許すか先に決める
- es-toolkit は元のキーを文字列化するが、C# はキーの型のまま。数値に戻す変換は要らない
- `null` の値は Python では `None` をキーにできるが、C# の `Dictionary` はキーに `null` を取れない。先に `Where(kv => kv.Value is not null)` で除く

## Test

`examples/ObjectInvertTests.cs`
