---
id: object-pick
lang: go
title: オブジェクトから指定したキーだけを取り出す
tags: [抽出, キー選択, 部分マップ, pick, select-keys, subset, projection]
lib: samber/lo
fn: lo.PickByKeys
since: "1.13.0"
verified: 2026-09-17
status: public
---

map から指定したキーのエントリだけを持つ新しい map を作る。レスポンスへ載せる項目の絞り込みやログ出力の項目選択に使う。

## Signature

```go
func PickByKeys[K comparable, V any, Map ~map[K]V](in Map, keys []K) Map
```

## Usage

```go
import "github.com/samber/lo"

m := map[string]int{"a": 1, "b": 2, "c": 3}
lo.PickByKeys(m, []string{"a", "c", "zz"})
// => map[string]int{"a": 1, "c": 3}
```

## Contract

- 入力 map を変更しない。返り値は新しい map（値は浅いコピー。ポインタ・スライス・map の値は同じ参照先を指す）
- 存在しないキーは無視され、返り値にそのキーは作られない。値がゼロ値でもエントリがあれば含まれる
- `keys` に重複があっても 1 つにまとまる
- `keys` が空・nil なら空の非 nil map（`len == 0`）。入力が nil map でも panic せず空の非 nil map を返す
- 返り値の型は入力と同じ名前付き map 型（`Map ~map[K]V`）
- panic しない

## Alternatives

- 条件で選ぶなら `lo.PickBy(m, func(key K, value V) bool)`、値で選ぶなら `lo.PickByValues`
- 除外する側を列挙したいなら `lo.OmitByKeys`（object-omit）
- 依存を増やせない場合は `out := make(map[K]V, len(keys))` に `if v, ok := m[k]; ok { out[k] = v }` するループ

## Pitfalls

- Python の `{k: d[k] for k in keys}` は存在しないキーで `KeyError` になるが、`PickByKeys` は黙って無視する。存在を保証したいなら `len(result) == len(keys)` を確認する
- es-toolkit の `pick` はキーの順序に規則があるが、Go の map に順序は無い。順序が要るなら `keys` の順で別途スライスに詰める
- stdlib の `maps.DeleteFunc` は **in place** で元の map を変える。元を残すなら使わない

## Test

`examples/object-pick_test.go`
