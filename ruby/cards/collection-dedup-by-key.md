---
id: collection-dedup-by-key
lang: ruby
title: キー関数で配列の重複を除去する
tags: [重複除去, ユニーク, 一意化, dedupe, uniq, distinct, unique-by]
lib: stdlib
fn: Array#uniq
since: "2.7"
verified: 2026-09-17
preserves_order: true
status: public
---

各要素からキーを取り出し、キーが同じ要素を 1 つに絞る。ID を持つハッシュの配列の重複除去に使う。

## Signature

```ruby
uniq { |element| ... } -> new_array / uniq -> new_array
```

## Usage

```ruby
users = [{ id: 1, name: "a" }, { id: 2, name: "b" }, { id: 1, name: "c" }]
users.uniq { |u| u[:id] }
# => [{id: 1, name: "a"}, {id: 2, name: "b"}]
```

## Contract

- 順序を保持する。同じキーの要素は **最初に出現したもの** を残す
- レシーバを変更しない。返り値は新しい配列（要素は同じ参照）
- ブロックは純粋関数であること。要素が 2 つ以上なら各要素につきちょうど 1 回、先頭から順に呼ばれる。要素が 1 つ以下なら呼ばれない
- ブロックを省略すると要素そのものがキーになる
- キーの比較は `Hash` のキーと同じ（`hash` と `eql?`）。`1` と `1.0` は別のキー、`"a"` と `:a` も別。配列やハッシュは内容で比較され、`hash` / `eql?` を定義していない独自クラスは同一オブジェクトのときだけ等しい
- 空配列を渡すと `[]` を返す
- 自身は例外を投げない（ブロックが投げた例外はそのまま伝わる）

## Alternatives

- その場で除去するなら `uniq!`（変更が無ければ `nil` を返すので、戻り値で連鎖しない）
- 配列以外の `Enumerable` にも同名の `Enumerable#uniq` があり、意味論は同じ
- 「最後」の要素を残したいなら `arr.reverse.uniq { ... }.reverse`、または `arr.to_h { |x| [key(x), x] }.values`
- 連続する重複だけをまとめればよい（ソート済み）なら `chunk_while { |a, b| key(a) == key(b) }.map(&:first)`

## Pitfalls

- 複合キーは配列で返せばよい（`[u[:a], u[:b]]`）。es-toolkit と違い配列は内容で比較されるので文字列に正規化する必要は無い
- es-toolkit の `uniqBy` は `NaN` 同士を等しいとみなすが、Ruby の `NaN` は `eql?` で等しくないので別々に計算した `NaN` は区別される（同じオブジェクトを 2 回入れたときにまとまるかは CRuby の内部最適化によるもので、仕様として当てにしない）。`NaN` を 1 つにまとめたいなら `uniq { |x| x.nan? ? :nan : x }` のようにキーを正規化する
- Python の `{key(x): x for x in xs}.values()` は **最後** の要素を残す。Ruby の `to_h { ... }.values` も同じく最後を残すので、`uniq` とは意味論が逆
- `uniq!` は変更が無いと `nil` を返す。メソッドチェーンの途中では `uniq` を使う

## Test

`examples/collection-dedup-by-key_test.rb`
