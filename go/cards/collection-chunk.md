---
id: collection-chunk
lang: go
title: 配列を固定長の小配列に分割する
tags: [分割, チャンク, バッチ, chunk, split, batch, iterator]
lib: stdlib
fn: slices.Chunk
since: "1.23"
verified: 2026-09-17
preserves_order: true
status: public
---

スライスを `n` 個ずつの部分スライスに切り分けるイテレータを返す。API のバッチ送信やページ分割で使う。

## Signature

```go
func Chunk[Slice ~[]E, E any](s Slice, n int) iter.Seq[Slice]
```

## Usage

```go
import "slices"

slices.Collect(slices.Chunk([]int{1, 2, 3, 4, 5}, 2))
// => [][]int{{1, 2}, {3, 4}, {5}}

for batch := range slices.Chunk(ids, 100) { // 100 件ずつ順に処理する
	send(batch)
}
```

## Contract

- 順序を保持する。各部分スライスの中も元の並び順のまま
- 遅延評価。返り値は `iter.Seq[Slice]` で、`for range` で 1 つずつ取り出す（途中で `break` してよい）。スライスとして受け取るには `slices.Collect` で確定させる。イテレータは何度でも走査できる
- 入力スライスを変更しないが、各部分スライスは元スライスの **ビュー**（同じ配列を共有）。部分スライスの要素を書き換えると元も変わる
- 各部分スライスの cap は長さに切り詰められている（`s[i:j:j]` 相当）。`append` すると必ず新しい配列が確保され、元スライスの後続要素は上書きされない
- 割り切れない場合、最後の部分スライスは `n` 未満になる。切り捨てない。`n` が長さ以上なら全体を含む部分スライスが 1 つだけ
- 空スライス・nil を渡すと何も返さない（`slices.Collect` の結果は `nil`）。空の部分スライスは決して返さない
- `n < 1` なら `Chunk` を呼んだ時点で panic する（イテレーションを始める前）
- 返り値の型は入力と同じ名前付きスライス型（`Slice ~[]E`）

## Alternatives

- 各チャンクを元と独立したコピーで、かつ `[][]T` として欲しいなら `lo.Chunk(s, n)`（`size <= 0` で panic）
- 重なる窓が欲しいなら `lo.Window`（collection-sliding-window）
- Go 1.22 以前は `for i := 0; i < len(s); i += n { end := min(i+n, len(s)); f(s[i:end:end]) }`

## Pitfalls

- 返り値は `[][]T` ではなくイテレータ。`len()` や添字は使えないので、件数が要るなら `slices.Collect` してから数える
- es-toolkit の `chunk` や Python の `itertools.batched` は要素をコピーした新しい配列・タプルを返すが、Go はビューを返す。チャンクを保持したまま元スライスを書き換える場合や goroutine に渡す場合は `slices.Clone` でコピーする
- `lo.Chunk` と違い、`n <= 0` の panic はイテレータを回したときではなく `slices.Chunk(...)` を呼んだ瞬間に起きる

## Test

`examples/collection-chunk_test.go`
