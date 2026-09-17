---
id: object-invert
lang: go
title: オブジェクトのキーと値を入れ替える
tags: [逆引き, キーと値の交換, 逆マッピング, invert, reverse-map, swap-keys, lookup]
lib: samber/lo
fn: lo.Invert
since: "1.13.0"
verified: 2026-09-17
status: public
---

map のキーと値を入れ替えた新しい map を作る。コード → 名称の表から名称 → コードの逆引き表を作るときに使う。

## Signature

```go
func Invert[K, V comparable](in map[K]V) map[V]K
```

## Usage

```go
import "github.com/samber/lo"

codes := map[string]int{"apple": 1, "pear": 2}
lo.Invert(codes)
// => map[int]string{1: "apple", 2: "pear"}
```

## Contract

- 入力 map を変更しない。返り値は新しい `map[V]K`
- 返り値のキーは元の値、返り値の値は元のキー。型はそのまま（文字列化しない）
- 値が重複していると返り値のエントリ数は元より少なくなり、どのキーが残るかは **決まらない**（元 map の走査順は未規定で、実行ごとに変わりうる）。残るのは元のキーのどれかで、それ以上は保証されない
- 値の型 `V` も `comparable` でなければならない（スライス・map・関数を値に持つ map はコンパイルエラー）
- 空・nil の map を渡すと空の非 nil map（`len == 0`）を返す
- panic しない

## Alternatives

- 重複する値をまとめたい（`map[V][]K`）なら `for k, v := range m { out[v] = append(out[v], k) }` のループ（各スライスの順序は不定なので、必要なら `slices.SortFunc` で並べる。`K` が `cmp.Ordered` なら `slices.Sort`）
- 重複時にどのキーを残すか決めたいなら、`slices.SortFunc` で決めた順にキーを並べてから自前のループで詰める（`K` が `cmp.Ordered` なら `slices.Sorted(maps.Keys(m))`）
- 依存を増やせない場合は `out := make(map[V]K, len(m))` に詰めるループ（挙動は同じ）

## Pitfalls

- es-toolkit の `invert` や Python の `{v: k for k, v in d.items()}` は「最後に処理したキーが残る」と決まっているが、Go は残るキーが実行ごとに変わる。値が一意である前提が崩れると再現しないバグになるので、`len(inverted) == len(m)` で重複を検出する
- 値の型に `comparable` 制約がある。`map[string][]string` のような map は `Invert` できない
- map に順序は無い。逆引き表を順序付きで扱うなら別途キーをソートする

## Test

`examples/object-invert_test.go`
