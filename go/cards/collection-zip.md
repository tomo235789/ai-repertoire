---
id: collection-zip
lang: go
title: 複数の配列を要素ごとに組にする
tags: [組にする, 対応付け, 並行走査, zip, pair, tuple, unzip]
lib: samber/lo
fn: lo.Zip2
since: "1.4.0"
verified: 2026-09-17
preserves_order: true
status: public
---

2 つのスライスを同じ位置どうしで `Tuple2` に組む。キー列と値列の対応付けや、並行して持つ 2 つの列の同時走査に使う。

## Signature

```go
func Zip2[A, B any](a []A, b []B) []Tuple2[A, B]
```

## Usage

```go
import "github.com/samber/lo"

pairs := lo.Zip2([]int{1, 2, 3}, []string{"a", "b"})
// => []lo.Tuple2[int, string]{{A: 1, B: "a"}, {A: 2, B: "b"}, {A: 3, B: ""}}
pairs[0].A, pairs[0].B // => 1, "a"
```

## Contract

- 順序を保持する。i 番目の `Tuple2` のフィールド `A` / `B` は各スライスの i 番目の要素
- 入力スライスを変更しない。返り値は新しいスライス（要素は値のコピー）
- 返り値の長さは **最も長い** 入力に合わせる。短い入力の足りない位置はその型の **ゼロ値**（`0`、`""`、`nil` など）で埋まる
- 引数は固定長 2 つ。3〜9 個は `lo.Zip3`〜`lo.Zip9` で、返り値は `Tuple3`〜`Tuple9`
- 両方とも空・nil なら空の非 nil スライス（`len == 0`）
- panic しない

## Alternatives

- 組にした後で加工するなら `lo.ZipBy2(a, b, func(a A, b B) R)`（長さの扱いは同じ）
- 逆操作（タプルのスライスを 2 つのスライスに戻す）は `lo.Unzip2`
- 短い方の長さで打ち切りたい（Python の `zip` 相当）なら `n := min(len(a), len(b))` として `lo.Zip2(a[:n], b[:n])`
- 依存を増やせない場合は `for i := range min(len(a), len(b))` のループで自前の構造体に詰める

## Pitfalls

- 足りない位置はゼロ値で埋まるので、`0` や `""` が正規の値なのか埋め草なのか結果からは区別できない。長さが揃う前提なら呼び出し側で先に検査する
- Python の `zip` は **最も短い** 入力で打ち切る。es-toolkit の `zip` は長い方に合わせて `undefined` で埋めるので、Go の挙動はこちらに近い（埋めるのがゼロ値である点だけ違う）
- 引数は可変長ではない。個数ごとに `Zip2`〜`Zip9` を使い分ける。返り値のフィールド名は `A`、`B`、`C`… で、`lo.T2(a, b)` でタプルを直接作れる

## Test

`examples/collection-zip_test.go`
