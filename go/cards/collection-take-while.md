---
id: collection-take-while
lang: go
title: 条件を満たす間だけ先頭から要素を取り出す
tags: [先頭から取り出す, 前置部分列, 打ち切り, take-while, prefix, until, drop-while]
lib: samber/lo
fn: lo.TakeWhile
since: "1.53.0"
verified: 2026-09-17
preserves_order: true
status: public
---

先頭から述語が真の間だけ要素を取り出し、最初に偽になった時点で打ち切る。ソート済みデータの先頭区間の抽出に使う。

## Signature

```go
func TakeWhile[T any, Slice ~[]T](collection Slice, predicate func(item T) bool) Slice
```

## Usage

```go
import "github.com/samber/lo"

lo.TakeWhile([]int{1, 2, 3, 1}, func(n int) bool { return n < 3 })
// => []int{1, 2}
```

## Contract

- 順序を保持する。返り値は元スライスの先頭部分（前置部分列）
- 入力スライスを変更しない。返り値は新しいスライス（要素は値のコピー）で、書き換えても元は変わらない
- `predicate` は純粋関数であること。先頭から順に、最初に `false` を返した要素まで呼ばれ、それ以降の要素には呼ばれない
- 最初に `false` になった要素は結果に含まない
- すべての要素で `true` なら全要素のコピー。先頭で `false`、空スライス、nil のときは空の非 nil スライス（`len == 0`）
- 返り値の型は入力と同じ名前付きスライス型（`Slice ~[]T`）
- panic しない

## Alternatives

- 先頭の条件を満たす部分を **捨てて** 残りが欲しいなら `lo.DropWhile`（v1.9.0）。`TakeWhile` と `DropWhile` の結果を連結すると元に戻る
- 依存を増やせない場合は stdlib で `i := slices.IndexFunc(s, func(x T) bool { return !pred(x) })` を取り、`i < 0` なら `s`、それ以外は `s[:i]`（ビュー）
- 位置に関係なく条件を満たす要素を集めるなら `lo.Filter`
- 先頭から個数で取るなら `s[:min(n, len(s))]`

## Pitfalls

- `Filter` ではない。途中で 1 つでも偽があれば、その後に真の要素があっても取り出さない
- `TakeWhile` は lo v1.53.0 で入った関数（`DropWhile` は v1.9.0 から）。古い lo では `slices.IndexFunc` の書き方を使う
- es-toolkit の `takeWhile`、Python の `itertools.takewhile` と同じ意味論。Python は遅延評価でイテレータを返すが、Go は即時にコピーを返す

## Test

`examples/collection-take-while_test.go`
