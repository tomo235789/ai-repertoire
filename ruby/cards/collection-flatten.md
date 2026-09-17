---
id: collection-flatten
lang: ruby
title: ネストした配列を指定の深さまで平坦化する
tags: [平坦化, 展開, 連結, flatten, flat, concat, flat-map]
lib: stdlib
fn: Array#flatten
since: "2.7"
verified: 2026-09-17
preserves_order: true
status: public
---

ネストした配列を `level` 段だけ開いて 1 本の配列にする。ページごとに取得した結果の連結などに使う。

## Signature

```ruby
flatten(level = nil) -> new_array
```

## Usage

```ruby
[1, [2, [3, [4]]]].flatten(1)
# => [1, 2, [3, [4]]]  1 段だけ開く

[1, [2, [3, [4]]]].flatten
# => [1, 2, 3, 4]  引数無しは全段
```

## Contract

- 順序を保持する。深さ優先で左から順に展開する
- レシーバを変更しない。返り値は新しい配列で、`level` より深い位置に残る配列は同じ参照
- `level` を省略（または `nil` / 負数）するとすべての段を展開する。`0` なら展開せず浅いコピーを返す
- 展開するのは配列（と `to_ary` を持つオブジェクト）だけ。文字列や `Hash` は展開しない
- 空配列、または空配列だけを含む配列を渡すと `[]` を返す
- 自分自身を含む再帰的な配列を全段展開すると `ArgumentError`。`level` を指定すればその段までは展開できる
- `level` が整数に変換できなければ `TypeError`。小数は `to_int` で切り捨てる

## Alternatives

- その場で展開するなら `flatten!`（変更が無ければ `nil` を返す）
- 各要素を変換しながら 1 段開くなら `flat_map { |x| ... }`（ブロックが配列を返したときだけ開く）
- 配列の配列を単に連結するなら `arrays.sum([])` や `arrays.inject(:+)`（`flatten(1)` の方が速く意図も明確）

## Pitfalls

- es-toolkit の `flatten` は `depth` の既定値が `1` だが、Ruby の `flatten` は引数無しで **全段** 展開する。1 段だけ開きたいときは `flatten(1)` を明示する
- Python の `itertools.chain.from_iterable` は文字列も文字に分解するが、Ruby の `flatten` は文字列を要素のまま残す
- `to_ary` を定義したオブジェクトは配列と同じく展開される
- `flatten!` は変更が無いと `nil` を返す。メソッドチェーンの途中では `flatten` を使う

## Test

`examples/collection-flatten_test.rb`
