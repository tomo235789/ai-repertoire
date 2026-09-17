---
id: object-omit
lang: csharp
title: オブジェクトから指定したキーを除いたコピーを作る
tags: [除外, キー削除, 部分辞書, omit, exclude-keys, drop-keys, without]
lib: stdlib
fn: Where + ToDictionary
since: "8.0"
verified: 2026-09-17
preserves_order: true
status: public
---

辞書から不要なキーを除いた新しい `Dictionary` を作る。パスワードなど外に出したくないフィールドの除去に使う。

## Signature

```csharp
d.Where(kv => !excluded.Contains(kv.Key)).ToDictionary()
```

## Usage

```csharp
using System.Linq;

var user = new Dictionary<string, object> { ["id"] = 1, ["name"] = "a", ["password"] = "x" };
var excluded = new HashSet<string> { "password" };
var rest = user.Where(kv => !excluded.Contains(kv.Key)).ToDictionary();
// => { ["id"] = 1, ["name"] = "a" }
```

## Contract

- 入力辞書を変更しない。返り値は新しい `Dictionary`（値は同じ参照）
- 即時評価。`ToDictionary` が返る時点で完成している
- 残ったキーは元の辞書の列挙順で追加される
- 存在しないキーを `excluded` に入れても無視される
- すべてのキーを除くと空の `Dictionary`。`excluded` が空なら元と同じ内容の別インスタンス
- 元の辞書の比較器は引き継がれず、返り値は `EqualityComparer<TKey>.Default`。引き継ぐなら `ToDictionary(kv => kv.Key, kv => kv.Value, d.Comparer)`（同じ比較器なので重複キーにはならない）
- 引数なしの `ToDictionary()` は .NET 8 から。それ以前は `ToDictionary(kv => kv.Key, kv => kv.Value)`
- `d` が `null` なら `Where` の呼び出し時に `ArgumentNullException`。`excluded` が `null` だと `d` に要素がある場合に列挙時（`ToDictionary` の中）で `NullReferenceException`、`d` が空なら投げない。どちらも `null` でなければ例外は投げない

## Alternatives

- 元の辞書を破壊的に変えてよいなら `d.Remove("password")`（存在しなくても `false` を返すだけで失敗しない）
- 値の条件で除くなら `d.Where(kv => kv.Value is not null).ToDictionary()`
- 残す側を列挙するなら object-pick

## Pitfalls

- `excluded` は `HashSet<string>` にする。配列でも動くが `Contains` が線形探索になる
- Python の `{k: v for k, v in d.items() if k not in keys}`、es-toolkit の `omit` と同じ意味論。`d.Remove(k)` は元を変えるので違う
- `excluded` を `StringComparer.OrdinalIgnoreCase` の `HashSet` にすれば大文字小文字を無視して除ける。元の辞書の比較器とは独立に決まる
- 元より緩い比較器（既定の辞書に `StringComparer.OrdinalIgnoreCase` など）を `ToDictionary` に渡すと、`"id"` と `"ID"` のように同一視されるキーが残った時点で `ArgumentException`。渡すなら `d.Comparer`

## Test

`examples/ObjectOmitTests.cs`
