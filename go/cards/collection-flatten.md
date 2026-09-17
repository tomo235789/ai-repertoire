---
id: collection-flatten
lang: go
title: ネストした配列を指定の深さまで平坦化する
tags: [平坦化, 展開, 連結, flatten, flat, concat, join-slices]
lib: stdlib
fn: slices.Concat
since: "1.22"
verified: 2026-09-17
preserves_order: true
status: public
---

複数のスライスを 1 つに連結する。`[][]T` を可変長引数で渡せば 1 段の平坦化になる。ページごとに取得した結果のまとめや、複数ソースの結合に使う。

## Signature

```go
func Concat[S ~[]E, E any](slices ...S) S
```

## Usage

```go
import "slices"

nested := [][]int{{1, 2}, {3}, {}, {4, 5}}
slices.Concat(nested...)
// => []int{1, 2, 3, 4, 5}
slices.Concat([]int{1}, []int{2, 3}) // => []int{1, 2, 3}
```

## Contract

- 順序を保持する。外側の並び順も内側の並び順も保つ
- 入力スライスを変更しない。返り値は新しいスライス（要素は値のコピー）。引数が 1 つでもコピーされる
- 開くのは 1 段だけ。`[][][]T` を渡すと `[][]T` になり、その要素の内側スライスは元と同じ配列を共有する
- 引数なし、またはすべて空・nil なら **`nil`** を返す（空の非 nil スライスではない）
- 引数に nil が混ざっていても長さ 0 として扱われ、panic しない
- 返り値の型は入力と同じ名前付きスライス型（`S ~[]E`）

## Alternatives

- `[][]T` をそのまま渡したいなら `lo.Flatten(nested)`（入力が空なら **非 nil** の空スライスを返す点だけ違う）
- 各要素を変換しながら 1 段開くなら `lo.FlatMap`
- Go 1.21 以前は `out := make([]T, 0, total)` に `append(out, inner...)` するループ

## Pitfalls

- Go はネストの深さが型で決まるので、es-toolkit の `flatten(arr, depth)` のような深さ指定は無い。`[][][]T` を全部開くなら `slices.Concat` を 2 回かける
- 結果が `nil` になりうる。`encoding/json` で `null` になるのを避けたい場合など、非 nil の空スライスが要るなら `lo.Flatten` を使うか `slices.Concat` の結果を検査する
- Python の `itertools.chain.from_iterable` と同じく 1 段だけ開く。ただし Python は遅延評価で、Go は即時に新しいスライスを作る

## Test

`examples/collection-flatten_test.go`
