---
id: collection-take-while
lang: ruby
title: 条件を満たす間だけ先頭から要素を取り出す
tags: [先頭から取り出す, 前置部分列, 打ち切り, take-while, prefix, until, drop-while]
lib: stdlib
fn: Enumerable#take_while
since: "2.7"
verified: 2026-09-17
preserves_order: true
status: public
---

先頭からブロックが真である間だけ要素を返し、最初に偽になった時点で打ち切る。ソート済み列から閾値未満の部分を取るときなどに使う。

## Signature

```ruby
take_while { |element| ... } -> new_array / take_while -> Enumerator
```

## Usage

```ruby
[1, 2, 3, 4, 1].take_while { |x| x < 3 }
# => [1, 2]

(1..).lazy.take_while { |x| x < 4 }.map { |x| x * 10 }.to_a
# => [10, 20, 30]  無限列も lazy で扱える
```

## Contract

- 順序を保持する。返り値は元配列の先頭部分（前置部分列）
- レシーバを変更しない。返り値は新しい配列（要素は同じ参照）
- ブロックは純粋関数であること。先頭から順に、最初に偽を返した要素まで呼ばれ、それ以降の要素には呼ばれない。走査もそこで止まるので、無限の `Enumerable` に直接使っても、ブロックが有限回のうちに偽を返すなら終了する（`(1..).take_while { true }` は終わらない）
- 真偽は Ruby の規則で判定する。偽になるのは `nil` と `false` だけで、`0` や `""` は真。最初に偽になった要素は結果に含まない
- すべての要素で真なら全要素の浅いコピー、先頭で偽なら `[]`。ブロック無しなら `Enumerator` を返す
- `Enumerator::Lazy` に対して呼ぶと `Enumerator::Lazy` を返し、後続の `map` などを含めて `first` / `to_a` まで評価しない
- 空配列を渡すと `[]` を返す
- 自身は例外を投げない（ブロックが投げた例外はそのまま伝わる）

## Alternatives

- 先頭の条件を満たす部分を **捨てて** 残りが欲しいなら `drop_while`。同じ配列に両方を使えば連結が元に戻る
- 位置に関係なく条件を満たす要素を集めるなら `select`
- 先頭から個数で取るなら `take(n)` / `first(n)`
- 最初に偽になる位置が欲しいなら `find_index { |x| !cond(x) }`

## Pitfalls

- `select` ではない。途中で 1 つでも偽があれば、その後に真の要素があっても取り出さない
- JavaScript / Python と違い `0` と `""` は真なので打ち切りにならない。空判定は `x.empty?` などを明示する
- es-toolkit の `takeWhile`、Python の `itertools.takewhile` と同じ意味論。Python は常に遅延評価だが、Ruby は `lazy` を付けたときだけ遅延する
- `Hash` に使うと要素は `[key, value]` の配列で、返り値も配列の配列。`Hash` に戻すなら `.to_h`

## Test

`examples/collection-take-while_test.rb`
