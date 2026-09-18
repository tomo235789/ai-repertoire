---
id: number-clamp
lang: rust
title: 数値を上限・下限の範囲に収める
tags: [範囲制限, 上限下限, 飽和, clamp, saturate, bound, min-max]
lib: stdlib
fn: Ord::clamp
since: "1.50"
verified: 2026-09-17
status: public
---

数値が範囲を超えていたら境界値に置き換える。ページ番号や音量、進捗率など有効範囲が決まっている値の補正に使う。`Ord` を実装する型のメソッドで、`f64` には同名の固有メソッドがある。

## Signature

```rust
fn clamp(self, min: Self, max: Self) -> Self where Self: Sized
```

## Usage

```rust
150.clamp(0, 100);       // => 100
(-5).clamp(0, 100);      // => 0
42.clamp(0, 100);        // => 42
2.5_f64.clamp(0.0, 1.0); // => 1.0（f64 の固有メソッド）
```

## Contract

- `x < min` なら `min`、`x > max` なら `max`、それ以外は `x` を返す。境界値は含む（`0.clamp(0, 100)` は `0`、`100.clamp(0, 100)` は `100`）
- `Ord` を実装する型すべてで使える（整数、`char`、`&str`、タプルなど）。値を消費し（`self`）、返り値は 3 引数のいずれか
- **`min > max` なら panic**（`5.clamp(10, 1)` は `min > max. min = 10, max = 1`）
- `f64` / `f32` は `Ord` ではなく固有メソッド `f64::clamp(self, min: f64, max: f64) -> f64` を使う。`x` が NaN なら NaN を返し、`min` か `max` が NaN、または `min > max` なら panic
- `f64::clamp` は範囲内なら `self` をそのまま返すと規定されており、`-0.0 < 0.0` は偽なので `(-0.0).clamp(0.0, 1.0)` は `-0.0` になる（零の符号に依存する処理は書かない）。`f64::INFINITY.clamp(0.0, 1.0)` は `1.0`
- 純粋関数。引数を変更しない

## Alternatives

- 片側だけなら `x.max(lo)`（下限）/ `x.min(hi)`（上限）。`f64` の `max` / `min` は NaN を無視して非 NaN 側を返す
- 範囲内かの判定だけなら `(lo..=hi).contains(&x)`
- 整数演算の結果を型の範囲に収めるなら `saturating_add` / `saturating_mul`

## Pitfalls

- TypeScript（es-toolkit の `clamp`）と Python の `max(lo, min(x, hi))` は `min > max` で黙って `max` を返すが、Rust は panic する。引数の取り違えは実行時に発覚する
- es-toolkit は境界が NaN でも NaN を返し、Python は境界の NaN を無視するが、Rust の `f64::clamp` は panic
- `x.min(hi).max(lo)` と書くと `lo > hi` のとき `lo` が返り、`x.max(lo).min(hi)` なら `hi` が返る。`clamp` に任せて panic で気付く方が安全
- es-toolkit の 2 引数形式（上限のみ）は無い。`x.min(hi)` を使う

## Test

`tests/number_clamp.rs`
