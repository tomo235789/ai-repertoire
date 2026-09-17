---
id: number-clamp
lang: ruby
title: 数値を上限・下限の範囲に収める
tags: [範囲制限, 上限下限, 飽和, clamp, saturate, bound, min-max]
lib: stdlib
fn: Comparable#clamp
since: "2.7"
verified: 2026-09-17
status: public
---

値が範囲を超えていたら境界値に置き換える。ページ番号や音量、進捗率など有効範囲が決まっている値の補正に使う。`Comparable` のメソッドなので数値以外（文字列、`Date` など）にも使える。

## Signature

```ruby
obj.clamp(min, max) -> obj | min | max
obj.clamp(range)    -> obj | range.begin | range.end
```

## Usage

```ruby
120.clamp(0, 100)  # => 100
-5.clamp(0, 100)   # => 0
42.clamp(0, 100)   # => 42
120.clamp(0..100)  # => 100
120.clamp(..100)   # => 100（上限のみ）
-5.clamp(0..)      # => 0（下限のみ）
```

## Contract

- 境界値は含む（`0.clamp(0, 100)` は `0`、`100.clamp(0, 100)` は `100`）
- 返り値は `self`・`min`・`max` のいずれかのオブジェクトそのもの。型変換はしない（`10.clamp(0.5, 9.5)` は `9.5` の `Float`、`5.clamp(0.5, 9.5)` は `5` の `Integer`）
- `min > max` なら `ArgumentError`（`min argument must be less than or equal to max argument`）
- `Range` 版は終端を含む範囲のみ。`0...10` や `...10` のように終端がある排他的な範囲は `ArgumentError`（`cannot clamp with an exclusive range`）。終端の無い `0...` は `0..` と同じに扱う（`5.clamp(0...)` は `5`、`-5.clamp(0...)` は `0`）
- `min` または `max` に `nil` を渡すとその側の制限を設けない（`5.clamp(nil, 10)` は `5`）。端無し Range `..hi` / `lo..` も同じ
- `self`・`min`・`max` のどれかが `Float::NAN` なら `ArgumentError`（`comparison of Float with 0 failed` など）。`NaN` は返らない
- 比較できない型（`Integer` と `String` など）を渡すと `ArgumentError`
- 引数を変更しない。純粋関数

## Alternatives

- `[[x, lo].max, hi].min` でも同じだが、`lo > hi` のとき `hi` が返り気付けない。`clamp` は例外で止まる
- 範囲内かの判定だけなら `(lo..hi).cover?(x)` か `x.between?(lo, hi)`
- 文字列や日付にもそのまま使える: `Date.new(2024, 1, 1).clamp(Date.new(2024, 2, 1), Date.new(2024, 3, 1))` は `2024-02-01`

## Pitfalls

- TypeScript 版（es-toolkit の `clamp`）と Python の `min(max(x, lo), hi)` は `lo > hi` のとき黙って `hi` を返すが、Ruby は `ArgumentError` を投げる
- es-toolkit の `clamp` は `NaN` が混ざると `NaN` を返すが、Ruby は例外を投げる。`NaN` になり得る値は先に `nan?` で除く
- es-toolkit の 2 引数形式 `clamp(value, max)` に相当する `5.clamp(10)` は `TypeError`（引数 1 個は `Range` のみ）。上限だけなら `x.clamp(..max)`
- 返り値は引数のオブジェクトそのものなので、`Integer` を `Float` の境界で挟むと結果の型が値によって変わる

## Test

`examples/number-clamp_test.rb`
