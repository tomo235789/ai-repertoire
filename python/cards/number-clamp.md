---
id: number-clamp
lang: python
title: 数値を上限・下限の範囲に収める
tags: [範囲制限, 上限下限, 飽和, clamp, saturate, bound, min-max]
lib: stdlib
fn: min / max
since: "3.0"
verified: 2026-09-17
status: public
---

数値が範囲を超えていたら境界値に置き換える。ページ番号や音量、進捗率など有効範囲が決まっている値の補正に使う。Python には組み込みの clamp が無い。

## Signature

```python
min(max(x, lo), hi)
```

## Usage

```python
def clamp(x, lo, hi):
    return min(max(x, lo), hi)

clamp(120, 0, 100)  # => 100
clamp(-5, 0, 100)   # => 0
clamp(42, 0, 100)   # => 42
```

## Contract

- 境界値は含む（`clamp(0, 0, 100)` は `0`、`clamp(100, 0, 100)` は `100`）
- 有限で比較可能な値なら、`lo > hi` の場合は常に `hi` が返る（`min` が最後に適用されるため）。`x` が `NaN` のときはこの限りでない（`NaN` を返す）
- 返り値は 3 つの引数のいずれかのオブジェクトそのもの。型変換はしない（`int` と `float` が混在すると選ばれた側の型）
- `x` が `NaN` なら `NaN` を返す。`lo` や `hi` が `NaN` のときはその境界だけが効かない（比較が常に `False` になり `max` / `min` は第 1 引数を返す。`clamp(10, nan, 5)` は `5`、`clamp(-1, nan, 5)` は `-1`）
- 引数を変更しない
- 比較できない型（`int` と `str` など）を渡すと `TypeError` を投げる

## Alternatives

- `max(lo, min(x, hi))` でも有限値では同じだが、`lo > hi` のときは `lo` が返る点と、`NaN` を含む場合の結果が違う
- `sorted((x, lo, hi))[1]` は `lo <= hi` なら同じ結果（`lo > hi` では中央値が返る）。意図が読み取りにくいので `min` / `max` を使う
- 範囲内かの判定だけなら `lo <= x <= hi`

## Pitfalls

- Python の組み込みに clamp は無い（3.14 時点でも `math.clamp` は無い）。関数として定義するか、その場で `min(max(...))` と書く
- TypeScript 版（es-toolkit の `clamp`）はどれか 1 つでも `NaN` なら `NaN` を返すが、Python は `x` が `NaN` のときだけ。境界に `NaN` が混ざっても気付けない
- es-toolkit の 2 引数形式 `clamp(value, max)` に相当するものは無い。上限だけなら `min(x, hi)`、下限だけなら `max(x, lo)`
- `lo > hi` の検証はしないので、引数の順序を取り違えると常に `hi` が返り気付きにくい

## Test

`examples/number-clamp_test.py`
