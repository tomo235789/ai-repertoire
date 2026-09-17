---
id: collection-group-by
lang: go
title: キー関数で配列をグループ化する
tags: [グループ化, 分類, 集計, group-by, categorize, bucket, map]
lib: samber/lo
fn: lo.GroupBy
since: "1.0.0"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、キーごとのスライスを持つ map にまとめる。種別ごとの集計や振り分けに使う。

## Signature

```go
func GroupBy[T any, U comparable, Slice ~[]T](collection Slice, iteratee func(item T) U) map[U]Slice
```

## Usage

```go
import "github.com/samber/lo"

lo.GroupBy([]int{1, 2, 3, 4, 5}, func(n int) string {
	return map[bool]string{true: "even", false: "odd"}[n%2 == 0]
})
// => map[string][]int{"even": {2, 4}, "odd": {1, 3, 5}}
```

## Contract

- 各グループのスライスは元の出現順のまま。ただし返り値は `map` なので、グループ（キー）の走査順は **未規定** で、実行のたびに変わりうる。順序が要るなら `slices.SortFunc` で決めた順にキーを並べる（キーが `cmp.Ordered` なら `slices.Sorted(maps.Keys(m))`）
- 入力スライスを変更しない。各グループは新しいスライス（要素は値のコピー）
- `iteratee` は純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる
- キーは `comparable` 型で、`map` のキーと同じ `==` で比較される
- 空スライス・nil を渡すと空の非 nil map（`len == 0`）を返す
- 存在しないキーを引くと nil スライス（`len == 0`）が返り、panic しない
- 返り値の型は `map[U]Slice`（各グループは入力と同じ名前付きスライス型）
- キーの値が厳密に比較可能なら panic しない。`U` が interface 型（`any` など）だと `comparable` を満たしてコンパイルは通るが、動的な型がスライスや map を含む値を返すと実行時に panic する（`hash of unhashable type`）

## Alternatives

- グループ化しながら要素を変換するなら `lo.GroupByMap(s, func(x T) (K, V))`（v1.50.0）
- グループを **初出順** のスライス `[]Slice` で欲しいなら `lo.PartitionBy`（キーは返らない）
- 件数だけ欲しいなら `lo.CountValuesBy`、キーが一意で 1 要素ずつ引きたいなら `lo.KeyBy`
- 依存を増やせない場合は `m := map[K][]T{}` に `m[key(x)] = append(m[key(x)], x)` するループ

## Pitfalls

- map の走査順は未規定で毎回変わりうる。テストの期待値や出力の順序を `for k, v := range m` に依存させない
- es-toolkit の `groupBy` は数値キーを文字列化して `1` と `'1'` を同じグループにするが、Go はキーの型がそのまま（`int` と `string` は別の map 型になる）
- Python の `itertools.groupby` は **連続する** 要素しかまとめない。`lo.GroupBy` はスライス全体をまとめる

## Test

`examples/collection-group-by_test.go`
