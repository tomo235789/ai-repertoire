---
id: object-pick
lang: csharp
title: オブジェクトから指定したキーだけを取り出す
tags: [抽出, キー選択, 部分辞書, pick, select-keys, subset, projection]
lib: stdlib
fn: Where + ToDictionary
since: "6.0"
verified: 2026-09-17
status: public
---

辞書から必要なキーだけを持つ新しい `Dictionary` を作る。API レスポンスの整形や、機密フィールドを含まない DTO の作成に使う。

## Signature

```csharp
keys.Where(d.ContainsKey).ToDictionary(k => k, k => d[k])
```

## Usage

```csharp
using System.Linq;

var user = new Dictionary<string, object> { ["id"] = 1, ["name"] = "a", ["password"] = "x" };
var keys = new[] { "id", "name" };
var picked = keys.Where(user.ContainsKey).ToDictionary(k => k, k => user[k]);
// => { ["id"] = 1, ["name"] = "a" }
```

## Contract

- 入力辞書を変更しない。返り値は新しい `Dictionary`（値は同じ参照）
- 即時評価。`ToDictionary` が返る時点で完成している
- 存在しないキーは `Where(d.ContainsKey)` で無視され、返り値にそのキーは作られない。値が `null` のキーは `null` のまま含まれる
- 返り値には `keys` の並び順で追加される。ただし `Dictionary` の列挙順は仕様として保証されない
- `keys` に重複があると `ToDictionary` が `ArgumentException` を投げる。重複しうるなら先に `Distinct()` を挟む
- 元の辞書の比較器は引き継がれない。`StringComparer.OrdinalIgnoreCase` の辞書から `"ID"` を `"id"` で取り出せるが、返り値は既定の比較器になる。引き継ぐなら `ToDictionary(k => k, k => d[k], d.Comparer)`
- `keys` が空なら空の `Dictionary` を返す
- `keys` が `null` なら `ArgumentNullException`。`keys` の要素に `null` があると `ContainsKey` が `ArgumentNullException` を投げる

## Alternatives

- 存在しないキーを黙って無視せず失敗させたいなら `keys.ToDictionary(k => k, k => d[k])`（`KeyNotFoundException`）
- 除外する側を列挙したいなら object-omit
- 型が決まっているならレコードや DTO クラスに詰め替える。クラスのプロパティを名前で選ぶ用途にはリフレクションが要るので、このイディオムは辞書向け

## Pitfalls

- `keys.ToDictionary(k => k, k => d.GetValueOrDefault(k))` と書くと、存在しないキーが `default` の値で含まれてしまう。es-toolkit の `pick` と同じ「無視」にするには `Where(d.ContainsKey)` が要る
- Python の `{k: d[k] for k in keys if k in d}` と同じ意味論
- 返り値を順序に依存して使わない。`Dictionary` の列挙順は `Remove` 後の追加で崩れる。順序が要るなら `keys` を別途持つ

## Test

`examples/ObjectPickTests.cs`
