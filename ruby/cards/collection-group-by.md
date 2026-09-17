---
id: collection-group-by
lang: ruby
title: キー関数で配列をグループ化する
tags: [グループ化, 分類, 集計, group-by, categorize, bucket, tally]
lib: stdlib
fn: Enumerable#group_by
since: "2.7"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、同じキーの要素を配列にまとめた `Hash` を作る。種別ごとの集計や画面のセクション分けに使う。

## Signature

```ruby
group_by { |element| ... } -> hash / group_by -> Enumerator
```

## Usage

```ruby
words = ["apple", "bob", "cat", "dove"]
words.group_by(&:size)
# => {5 => ["apple"], 3 => ["bob", "cat"], 4 => ["dove"]}
```

## Contract

- 順序を保持する。各グループの配列は元の出現順で、`Hash` のキーもグループの初出順に並ぶ
- レシーバを変更しない。返り値は新しい `Hash`（デフォルト値無し）で、要素は同じ参照
- 即時評価。返る時点で入力をすべて読み終えている。ブロック無しなら `Enumerator` を返す
- ブロックは純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる
- キーの比較は `Hash` のキーと同じ（`hash` と `eql?`）。`1` と `1.0` は別のグループになる。`nil` もキーにできる
- 空配列を渡すと `{}` を返す
- 自身は例外を投げない（ブロックが投げた例外はそのまま伝わる）

## Alternatives

- 件数だけなら `tally`（要素そのものがキー）、キー関数で数えるなら `map { ... }.tally`
- **連続する** 要素だけをまとめるなら `chunk_while { |a, b| ... }` / `slice_when { |a, b| ... }`（配列の配列を返す。ソート済みの列を区切るときに使う）
- 各グループを別の値に変換するなら `group_by { ... }.transform_values { |xs| ... }`
- 2 つに分けるだけなら `partition`（collection-partition）

## Pitfalls

- 返り値の `Hash` にデフォルト値は無く、存在しないキーは `nil` を返す。`h.fetch(k, [])` か `Hash.new { |h, k| h[k] = [] }` に詰め直して使う
- es-toolkit の `groupBy` は数値キーを文字列化して `1` と `"1"` を同じグループにするが、Ruby では別のキー。`1` と `1.0` も別（Python では同じ）
- Python の `itertools.groupby` に相当するのは `chunk_while` / `slice_when` で、`group_by` は事前ソート無しで配列全体をまとめる

## Test

`examples/collection-group-by_test.rb`
