---
id: collection-sort-by
lang: ruby
title: 複数のキーで配列を昇順に並べ替える
tags: [並べ替え, ソート, 整列, sort, sort-by, order-by, unstable-sort]
lib: stdlib
fn: Enumerable#sort_by
since: "2.7"
verified: 2026-09-17
preserves_order: false
status: public
---

ブロックの返り値で要素を昇順に並べ替えた新しい配列を作る。複数キーは配列を返す。

## Signature

```ruby
sort_by { |element| ... } -> new_array / sort_by -> Enumerator
```

## Usage

```ruby
users = [{ name: "b", age: 30 }, { name: "a", age: 30 }, { name: "c", age: 20 }]
users.sort_by { |u| [u[:age], u[:name]] }
# => [{name: "c", age: 20}, {name: "a", age: 30}, {name: "b", age: 30}]
```

## Contract

- **不安定ソート**。キーが等しい要素の相対順は保証されない（公式リファレンスに明記）。元の順を保ちたいなら `sort_by.with_index { |x, i| [key(x), i] }` で添字を最後のキーに加える
- レシーバを変更しない。返り値は新しい配列（要素は同じ参照）
- 即時評価。ブロック無しなら `Enumerator` を返す
- ブロックは純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる（比較のたびではない）
- 複数キーは配列を返す。左から順に `<=>` で比較し、前が等しいときだけ次で比較する
- 昇順のみ。数値キーは符号反転で降順にできる
- 空配列を渡すと `[]` を返す
- キー同士が `<=>` で比較できなければ `ArgumentError`（`nil` と数値、数値と文字列、`NaN` の混在など。配列キーの中に混ざっていても同じ）

## Alternatives

- その場で並べ替えるなら `sort_by!`（`Array` のみ）
- 比較関数を自分で書くなら `sort { |a, b| ... }`。キーの計算が重いときは `sort_by` の方が速い（Schwartzian transform）
- 最小・最大の 1 件だけなら `min_by` / `max_by`、上位 n 件なら `min_by(n)` / `max_by(n)`
- 降順は `sort_by { ... }.reverse`（同じキーの並びも反転する点に注意）

## Pitfalls

- es-toolkit の `sortBy` と Python の `sorted` は安定ソートだが、Ruby の `sort_by`（と `sort`）は不安定。同じキーの要素の順に意味があるなら必ず添字を加える
- es-toolkit は `null` / `undefined` を末尾に置くが、Ruby は `nil` が混ざると `ArgumentError`。末尾に置くなら `[x.nil? ? 1 : 0, x || 0]` のように配列キーで先に振り分ける
- 文字列はバイト順で、大文字が小文字より前に来る（`["A", "B", "a", "b"]`）。大小を無視するなら `x.downcase` をキーにする
- `Hash` に使うと要素は `[key, value]` の配列で、返り値も配列の配列。`Hash` に戻すなら `.to_h`

## Test

`examples/collection-sort-by_test.rb`
