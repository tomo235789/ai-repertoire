---
id: object-omit
lang: go
title: オブジェクトから指定したキーを除いたコピーを作る
tags: [除外, キー削除, 部分マップ, omit, exclude-keys, drop-keys, without]
lib: samber/lo
fn: lo.OmitByKeys
since: "1.13.0"
verified: 2026-09-17
status: public
---

map から指定したキーを除いた新しい map を作る。パスワードや内部用フィールドを落としてから外へ渡すときに使う。

## Signature

```go
func OmitByKeys[K comparable, V any, Map ~map[K]V](in Map, keys []K) Map
```

## Usage

```go
import "github.com/samber/lo"

user := map[string]string{"name": "alice", "password": "x", "role": "admin"}
lo.OmitByKeys(user, []string{"password", "zz"})
// => map[string]string{"name": "alice", "role": "admin"}
```

## Contract

- 入力 map を変更しない。返り値は全エントリをコピーした新しい map から指定キーを削除したもの（値は浅いコピー。ポインタ・スライス・map の値は同じ参照先を指す）
- 存在しないキーを指定しても無視される
- すべてのキーを除くと空の非 nil map（`len == 0`）。`keys` が空・nil なら元と同じ内容の別の map
- 入力が nil map でも panic せず空の非 nil map を返す
- 返り値の型は入力と同じ名前付き map 型（`Map ~map[K]V`）
- panic しない

## Alternatives

- 条件で除くなら `lo.OmitBy(m, func(key K, value V) bool)`、値で除くなら `lo.OmitByValues`
- 残す側を列挙するなら `lo.PickByKeys`（object-pick）
- 元の map を破壊的に変えてよいなら stdlib の `delete(m, k)`（存在しなくても失敗しない）か `maps.DeleteFunc`
- 依存を増やせない場合は `maps.Clone(m)` してから `delete` する

## Pitfalls

- 除くキーが少なくても全エントリをコピーするので、コストは map の大きさに比例する。大きな map から 1 つだけ除くことを繰り返すなら設計を見直す
- `delete` / `maps.DeleteFunc` は元の map を変える。TypeScript 版（es-toolkit の `omit`）や Python の辞書内包表記と同じ「コピーを作る」意味論が要るなら `OmitByKeys`
- map に順序は無いので、es-toolkit の「残ったキーの順序は元のまま」に相当する保証は無い

## Test

`examples/object-omit_test.go`
