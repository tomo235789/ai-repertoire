---
id: collection-sliding-window
lang: go
title: 配列をスライディングウィンドウで走査する
tags: [スライディングウィンドウ, 移動窓, 移動平均, sliding-window, windowed, rolling, pairwise]
lib: samber/lo
fn: lo.Window
since: "1.53.0"
verified: 2026-09-17
preserves_order: true
status: public
---

スライスを `size` 個ずつ 1 要素ずつずらした窓の列にする。移動平均や隣接要素の比較に使う。

## Signature

```go
func Window[T any, Slice ~[]T](collection Slice, size int) []Slice
```

## Usage

```go
import "github.com/samber/lo"

lo.Window([]int{1, 2, 3, 4}, 2)
// => [][]int{{1, 2}, {2, 3}, {3, 4}}
lo.Window([]int{1, 2}, 3)
// => [][]int{}
```

## Contract

- 順序を保持する。窓は先頭から 1 つずつずれた開始位置で並び、窓の中も元の並び順
- 入力スライスを変更しない。各窓は **新しいスライス**（要素は値のコピー）で、窓を書き換えても元や他の窓は変わらない
- ずらす幅は常に 1（`step` 引数は無い）。隣り合う窓は `size - 1` 個の要素を共有する
- `size` に満たない末尾の窓は **作られない**。長さが `size` 未満なら空の非 nil スライス（`len == 0`）、長さが `size` と同じなら窓 1 つ
- 空スライス・nil を渡すと空の非 nil スライス
- `size <= 0` なら panic する
- 返り値の型は `[]Slice`（各窓は入力と同じ名前付きスライス型）

## Alternatives

- ずらす幅を指定したいなら `lo.Sliding(s, size, step)`（`Window` は `Sliding(s, size, 1)` と同じ。`step` で飛ばした要素や末尾の不完全な窓は捨てられる）
- 重ならない分割は `slices.Chunk`（collection-chunk）
- 依存を増やせない場合は `for i := 0; i+size <= len(s); i++ { f(s[i : i+size : i+size]) }`（各窓はコピーではなくビュー）

## Pitfalls

- `Window` / `Sliding` は lo v1.53.0 で入った関数。それ以前の lo には無い
- es-toolkit の `windowed` の `partialWindows: true` や more-itertools の `windowed` の `fillvalue` に相当する機能は無い。末尾の短い窓が要るなら自前で書く
- 各窓がコピーなのでメモリは `len(s) * size` に比例する。長いスライスに大きな窓を取るならビューを返す自前のループにする

## Test

`examples/collection-sliding-window_test.go`
