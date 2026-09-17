---
id: collection-partition
lang: ruby
title: 条件で配列を 2 つに振り分ける
tags: [振り分け, 分割, 二分, partition, split, separate, filter]
lib: stdlib
fn: Enumerable#partition
since: "2.7"
verified: 2026-09-17
preserves_order: true
status: public
---

ブロックの真偽で要素を 2 つの配列に分ける。有効・無効の振り分けや成功・失敗の仕分けに使う。

## Signature

```ruby
partition { |element| ... } -> [true_array, false_array] / partition -> Enumerator
```

## Usage

```ruby
evens, odds = [1, 2, 3, 4, 5].partition(&:even?)
evens # => [2, 4]
odds  # => [1, 3, 5]
```

## Contract

- 順序を保持する。両方の配列とも元の並び順のまま
- レシーバを変更しない。返り値は新しい配列 2 つの組（要素は同じ参照）
- 返り値は `[真の要素, 偽の要素]` の順。**真が先**
- 即時評価。ブロック無しなら `Enumerator` を返す
- ブロックは純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる
- 真偽は Ruby の規則で判定する。偽になるのは `nil` と `false` だけで、`0` や `""` は真側に入る
- 空配列を渡すと `[[], []]` を返す
- 自身は例外を投げない（ブロックが投げた例外はそのまま伝わる）

## Alternatives

- 片方だけ要るなら `select` / `reject`。両方要るときに 2 回走査せずに済むのが `partition`
- 条件を満たす要素を変換しながら取り出すなら `filter_map { |x| f(x) if cond(x) }`（`nil` / `false` を落とす）
- 3 つ以上に分けるなら `group_by`（collection-group-by）

## Pitfalls

- es-toolkit の `partition` と同じ `[真, 偽]` の順だが、Python の `more_itertools.partition` は `(偽, 真)` の順。分割代入の順を取り違えない
- JavaScript / Python と違い `0` と `""` は真。数値や文字列の空判定は `x.zero?` / `x.empty?` を明示する
- `Hash` に使うと要素は `[key, value]` の配列になり、返り値も配列の配列。`Hash` に戻すなら `.map(&:to_h)`

## Test

`examples/collection-partition_test.rb`
