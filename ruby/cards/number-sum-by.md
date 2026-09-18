---
id: number-sum-by
lang: ruby
title: 配列の各要素から取り出した数値を合計する
tags: [合計, 集計, 合算, sum, sum-by, total, aggregate]
lib: stdlib
fn: Enumerable#sum
since: "2.4"
verified: 2026-09-17
status: public
---

各要素から数値を取り出して合計する。オブジェクト配列の数量や金額の集計に使う。`Float` は補正付きで加算される。

## Signature

```ruby
enum.sum(init = 0) { |element| ... } -> object
```

## Usage

```ruby
items = [{ name: "a", qty: 2 }, { name: "b", qty: 3 }]
items.sum { |item| item[:qty] }
# => 5
([0.1] * 10).sum
# => 1.0（inject(:+) だと 0.9999999999999999）
```

## Contract

- 入力を変更しない
- ブロックは純粋関数であること。各要素につきちょうど 1 回、先頭から順に呼ばれる
- 空なら `init` を返す。既定は `0`（`Integer`）
- 型変換はしない。結果は `init` に各要素を `+` で足したものと同じで、`init`（既定は `0`）と要素の `+` が互換でないと `TypeError`（`[1, nil].sum` は `nil can't be coerced into Integer`）。`String` の列でも `init` を `""` にすれば連結できる（`["a", "b"].sum("")` は `"ab"`）。`Integer` と `Float` が混在すると `Float`。ただし「要素ごとに `+` を呼ぶ」ことは実装保証ではなく、`Integer` / `Float` の列や整数 `Range`（ブロック無し）は最適化され、`Integer#+` や `each` を再定義しても呼ばれない
- `Float` の合計は Kahan-Babuska 補正付きで、`([0.1] * 10).sum` は `1.0`、`[0.1, 0.2, 0.3].sum` は `0.6`、`[1e100, 1.0, -1e100].sum` は `1.0`。`inject(:+)` は素朴な加算で `0.9999999999999999` / `0.6000000000000001` / `0.0`。ただし `[0.1, 0.2].sum` は `0.30000000000000004`（正しく丸めた結果）
- 要素に `Float::NAN` があれば `NaN`。`Float::INFINITY` と `-Float::INFINITY` を両方含むと `NaN`
- `Rational` / `BigDecimal` の合計はそのまま動く（`[1, Rational(1, 2)].sum` は `(3/2)`）。`Float` と混ぜると `Float` / `BigDecimal` に寄る
- `Range` や `Hash` でも使える（`(1..4).sum { |x| x * 2 }` は `20`、`hash.sum { |k, v| v }`）
- 自身が投げるのは上記の `TypeError`。要素の `+` / `coerce` や列挙処理（`each`）が投げた例外、ブロックが投げた例外はそのまま伝播する

## Alternatives

- 文字列の連結は `strings.sum("")` でも動くが `strings.join` を使う。配列の連結は `arrays.sum([])` より `arrays.flatten(1)`（`sum` は毎回新しいオブジェクトを作る）
- 平均は number-mean。最大・最小の要素は `max_by` / `min_by`
- 要素がそのまま数値なら `arr.sum`（ブロック無し）

## Pitfalls

- TypeScript 版（es-toolkit の `sumBy`）は取り出した値が `undefined` なら `NaN`、文字列なら連結になるが、Ruby は `TypeError` で止まる。キーが欠けている要素があるなら `item[:qty].to_i` や `item.fetch(:qty, 0)` で補う
- Python の `sum` と同じ意味論（3.12 以降は Python も補正付き加算）。空なら `0`
- `Float` の結果が欲しいのに要素がすべて `Integer` なら `sum(0.0)` と `init` を指定する。`init` を `0.0` にしても補正は同じ
- 金額など誤差を許せない値は整数（最小単位）か `BigDecimal` で合計する

## Test

`examples/number-sum-by_test.rb`
