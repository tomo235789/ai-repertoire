---
id: collection-partition
lang: go
title: 条件で配列を 2 つに振り分ける
tags: [振り分け, 分割, 二分, partition, split, separate, filter-reject]
lib: samber/lo
fn: lo.FilterReject
since: "1.41.0"
verified: 2026-09-17
preserves_order: true
status: public
---

述語が真の要素と偽の要素を 1 回の走査で 2 つのスライスに分ける。有効・無効の振り分けや成功・失敗の仕分けに使う。

## Signature

```go
func FilterReject[T any, Slice ~[]T](collection Slice, predicate func(T, int) bool) (kept, rejected Slice)
```

## Usage

```go
import "github.com/samber/lo"

evens, odds := lo.FilterReject([]int{1, 2, 3, 4}, func(n int, _ int) bool { return n%2 == 0 })
// evens => []int{2, 4}
// odds  => []int{1, 3}
```

## Contract

- 順序を保持する。両方のスライスとも元の並び順のまま
- 入力スライスを変更しない。返り値は新しいスライス 2 つ（要素は値のコピー）
- 返り値の順は `(kept, rejected)`。**真が先**
- `predicate` は `(要素, 添字)` を受け取る。純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる
- 空スライス・nil を渡すと両方とも空の非 nil スライス（`len == 0`）
- 返り値の型は入力と同じ名前付きスライス型（`Slice ~[]T`）
- panic しない

## Alternatives

- 片方だけ要るなら `lo.Filter` / `lo.Reject`（同じ `(item, index)` 形の述語）
- 3 つ以上に分けるなら `lo.GroupBy`（collection-group-by）
- 依存を増やせない場合は `for` ループで 2 つのスライスに `append` する。stdlib の `slices.DeleteFunc` は **in place** で条件に合う要素を消すので意味が違う

## Pitfalls

- 述語は添字付きの `func(T, int) bool`。`func(T) bool` は渡せないので `_ int` で受ける
- es-toolkit の `partition` と同じ `[真, 偽]` の順だが、Python の more-itertools `partition` は `(偽, 真)` の順で返す。移植時に順を取り違えない
- `slices.DeleteFunc` は残った要素を元スライスの先頭に詰め直し、後ろの要素をゼロ値にする。元を残したい場合に使わない

## Test

`examples/collection-partition_test.go`
