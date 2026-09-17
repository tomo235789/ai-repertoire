---
id: collection-dedup-by-key
lang: go
title: キー関数で配列の重複を除去する
tags: [重複除去, ユニーク, 一意化, dedupe, uniq, distinct, unique-by]
lib: samber/lo
fn: lo.UniqBy
since: "1.0.0"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、キーが同じ要素を 1 つに絞る。ID を持つ構造体スライスの重複除去に使う。

## Signature

```go
func UniqBy[T any, U comparable, Slice ~[]T](collection Slice, iteratee func(item T) U) Slice
```

## Usage

```go
import "github.com/samber/lo"

type User struct{ ID int; Name string }
users := []User{{1, "a"}, {2, "b"}, {1, "c"}}
lo.UniqBy(users, func(u User) int { return u.ID })
// => []User{{1, "a"}, {2, "b"}}
```

## Contract

- 順序を保持する。同じキーの要素は **最初に出現したもの** を残す
- 入力スライスを変更しない。返り値は新しいスライス（要素は値のコピー。ポインタやスライスを含む要素は同じ参照先を指す）
- `iteratee` は純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる
- キーは `comparable` 型で、`map` のキーと同じ `==` で比較される。`NaN` は自身と等しくないので毎回別のキー扱いになり除去されない
- 空スライス・nil を渡すと空の非 nil スライス（`len == 0`）を返す
- 返り値の型は入力と同じ名前付きスライス型（`Slice ~[]T`）
- キーの値が厳密に比較可能なら panic しない。`U` が interface 型（`any` など）だと `comparable` を満たしてコンパイルは通るが、動的な型がスライスや map を含む値を返すと実行時に panic する（`hash of unhashable type`）

## Alternatives

- 要素そのものがキーなら `lo.Uniq(s)`
- ソート済みのスライスなら stdlib の `slices.Compact` / `slices.CompactFunc`（**連続する** 重複だけ除く。in place）
- 重複している要素の方を知りたいなら `lo.FindDuplicatesBy`
- キー関数がエラーを返しうるなら `lo.UniqByErr`
- 依存を増やせない場合は `seen := map[K]struct{}{}` を使ったループ

## Pitfalls

- キーは `comparable` でなければならず、スライスや map をそのままキーにできない。複合キーは構造体（`struct{ A string; B int }`）にまとめる。文字列連結でキーを作ると区切り文字を含む値で衝突する
- `slices.Compact` は隣接した重複しか除かない。ソートしていないスライスに使うと重複が残る
- es-toolkit の `uniqBy` と同じ意味論（最初を残す）。Python の `{key(x): x for x in xs}.values()` は **最後** を残すので逆

## Test

`examples/collection-dedup-by-key_test.go`
