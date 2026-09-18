---
id: collection-chunk
lang: ruby
title: 配列を固定長の小配列に分割する
tags: [分割, チャンク, バッチ, chunk, split, batch, each-slice]
lib: stdlib
fn: Enumerable#each_slice
since: "3.1"
verified: 2026-09-17
preserves_order: true
status: public
---

配列を `n` 個ずつの小配列に切り分ける。API のバッチ送信やページ分割で使う。

## Signature

```ruby
each_slice(n) { |slice| ... } -> self / each_slice(n) -> Enumerator
```

## Usage

```ruby
[1, 2, 3, 4, 5].each_slice(2).to_a
# => [[1, 2], [3, 4], [5]]

[1, 2, 3, 4, 5].each_slice(2) { |batch| p batch }
# 出力: [1, 2] / [3, 4] / [5]。戻り値はレシーバ自身
```

## Contract

- 順序を保持する。各小配列の中も元の並び順のまま
- レシーバを変更しない。各小配列は新しい配列で、要素は同じ参照
- ブロック無しなら `Enumerator` を返す。`to_a` で配列の配列になり、`first(k)` などで必要な分だけ入力を読み進める
- ブロック付きならレシーバ自身を返す（3.0 以前は `nil`）
- 割り切れない場合、最後の小配列は `n` 未満になる。切り捨てない。`n` が要素数より大きければ全体が 1 つの小配列になる
- 空配列なら何も yield せず、`to_a` は `[]`
- `n` が `0` 以下なら `ArgumentError`。整数でない値は `to_int` で変換され（`1.5` → `1`）、変換できない値は `TypeError`

## Alternatives

- 重なりのある窓が欲しいなら `each_cons(n)`（collection-sliding-window）。`each_slice` は重ならない
- 添字で切るなら `(0...arr.size).step(n).map { |i| arr[i, n] }`。`each_slice` の方が短く、Range や Hash など任意の `Enumerable` に使える
- 連続する要素を条件でまとめるなら `chunk_while` / `slice_when`

## Pitfalls

- `each_cons(n)` と混同しやすい。`each_cons` は 1 つずつずらした重なる窓で、`n` 未満の末尾は出さない
- es-toolkit の `chunk` は小数の `size` を例外にするが、Ruby は `to_int` で切り捨てて受け付ける
- 文字列を分割したい場合は `str.chars.each_slice(n).map(&:join)`。`each_slice` は `String` に直接は使えない
- Python の `itertools.batched`、es-toolkit の `chunk` と同じ意味論（最後が短くなる）

## Test

`examples/collection-chunk_test.rb`
