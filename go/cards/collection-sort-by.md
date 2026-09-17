---
id: collection-sort-by
lang: go
title: 複数のキーで配列を昇順に並べ替える
tags: [並べ替え, ソート, 整列, sort, sort-by, order-by, stable-sort]
lib: stdlib
fn: slices.SortStableFunc
since: "1.21"
verified: 2026-09-17
preserves_order: true
status: public
---

比較関数でスライスをその場で安定ソートする。複数キーは `cmp.Or` と `cmp.Compare` を組み合わせて左から順に比較する。

## Signature

```go
func SortStableFunc[S ~[]E, E any](x S, cmp func(a, b E) int)
```

## Usage

```go
import ("cmp"; "slices")

type User struct{ Name string; Age int }
users := []User{{"b", 30}, {"a", 20}, {"c", 30}}
slices.SortStableFunc(users, func(x, y User) int {
	return cmp.Or(cmp.Compare(x.Age, y.Age), cmp.Compare(x.Name, y.Name)) // Age → Name の順
})
// users => []User{{"a", 20}, {"b", 30}, {"c", 30}}
```

## Contract

- 安定ソート。比較関数が `0` を返す要素は元の相対順を保つ
- **破壊的**。入力スライスをその場で並べ替え、返り値は無い。元を残したいなら先に `slices.Clone` する
- `cmp.Compare(a, b)` で昇順、引数を入れ替えた `cmp.Compare(b, a)` で降順。キーごとに向きを変えられる
- `cmp.Or(c1, c2, ...)`（Go 1.22）は最初の非 0 を返すので、左のキーが等しいときだけ右のキーで比較される
- 比較関数は比較のたびに呼ばれる（各要素 1 回ではない）。純粋で、strict weak ordering を満たすこと
- `cmp.Compare` の文字列比較はバイト順。浮動小数の `NaN` は他のどの値より小さく、`NaN` 同士は等しいとみなす（並びが定まる）
- 空スライス・nil を渡すと何もせず、panic しない

## Alternatives

- 元を変えずに並べ替えた新しいスライスが欲しいなら `slices.SortedStableFunc(slices.Values(s), cmp)`（Go 1.23）
- 安定性が不要なら `slices.SortFunc`（同じキーの要素の順序は保証されない）
- 単一キーで要素自体が `cmp.Ordered` なら `slices.Sort(s)`
- Go 1.20 以前は `sort.SliceStable(s, func(i, j int) bool)`

## Pitfalls

- es-toolkit の `sortBy` や Python の `sorted` は新しい配列を返すが、`SortStableFunc` は引数をその場で書き換える。関数の引数で受け取ったスライスをそのまま渡すと呼び出し元の並びも変わる
- 文字列はバイト順で、大文字が小文字より前に来る。日本語や大小無視の自然な順は `golang.org/x/text/collate` か `strings.ToLower` したキーで比較する
- es-toolkit の `sortBy` のように `null` / `undefined` を末尾に置く規則は無い。ポインタやオプショナルなフィールドの並び位置は比較関数で明示する（`bool` は `cmp.Ordered` ではないので `cmp.Compare(x == nil, y == nil)` とは書けず、`0` / `1` の `int` に変換して比較する）
- `slices.Sort` / `slices.SortFunc` は不安定。同じキーの要素の順序に意味があるなら必ず `SortStableFunc` を使う

## Test

`examples/collection-sort-by_test.go`
