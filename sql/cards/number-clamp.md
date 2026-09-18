---
id: number-clamp
lang: sql
title: 数値を上限・下限の範囲に収める
tags: [範囲制限, 上限下限, 飽和, スカラー関数, clamp, saturate, least-greatest, min-max]
lib: sqlite
fn: MIN / MAX
since: "3.0"
verified: 2026-09-17
status: public
---

列の値が範囲を超えていたら境界値に置き換える。sqlite では 2 引数以上の `MIN` / `MAX` が行ごとのスカラー関数になるのでそれを入れ子にする。duckdb / PostgreSQL は `LEAST` / `GREATEST`。

## Signature

```sql
MIN(MAX(x, lo), hi)
```

## Usage

```sql
WITH t(v) AS (VALUES (120), (-5), (42), (NULL))
SELECT v, MIN(MAX(v, 0), 100) AS clamped FROM t ORDER BY v;
-- => (NULL, NULL), (-5, 0), (42, 42), (120, 100)   -- sqlite
```

## Contract

- sqlite の `MIN` / `MAX` は引数が 2 つ以上だとスカラー関数（行ごとに引数の最小・最大）、1 つだと集計関数。同名で意味が変わる
- 境界値は含む（`MIN(MAX(0, 0), 100)` は `0`、`MIN(MAX(100, 0), 100)` は `100`）
- `lo > hi` のときは `x` が非 `NULL` なら常に `hi`（`MIN` が最後に適用されるため）。`x` が `NULL` なら sqlite は `NULL`（`MIN(MAX(NULL, 100), 0)` → `NULL`）、duckdb の `LEAST(GREATEST(NULL, 100), 0)` は `NULL` を無視して `0`
- `NULL` の扱いは方言で違う。sqlite のスカラー `MIN` / `MAX` は引数に 1 つでも `NULL` があると `NULL`（`MAX(NULL, 0)` → `NULL`）。duckdb の `GREATEST` / `LEAST` は `NULL` を無視して残りで比較する（`GREATEST(NULL, 0)` → `0`、`LEAST(GREATEST(NULL, 0), 100)` → `0`、全部 `NULL` なら `NULL`）
- 返り値は選ばれた引数の値と型そのまま（sqlite: `MIN(MAX(5, 0), 100)` は integer、`MIN(MAX(1.5, 0), 100)` は real の `1.5`）
- sqlite は型が混ざると型の順序で比較する（数値 < TEXT < BLOB）。`MAX('5', 0)` は `'5'`、`MIN('5', 100)` は `100` になり、文字列を渡すと期待と違う結果になる
- duckdb では `MIN(MAX(v, 0), 100)` は書けない。duckdb の `MAX(x, n)` は「上位 n 件のリスト」を返す集計関数で、入れ子にすると `aggregate function calls cannot be nested` エラー。`LEAST(GREATEST(v, 0), 100)` を使う
- duckdb で `NaN` は `GREATEST(NaN, 0)` → `NaN`、`LEAST(NaN, 100)` → `100` なので clamp の結果は `100`（`NaN` は最大値扱い）

## Alternatives

- duckdb / PostgreSQL / MySQL / BigQuery: `LEAST(GREATEST(v, lo), hi)`。`NULL` の扱いは方言で違い、MySQL は引数に `NULL` があると `NULL` を返すと書かれる
- 方言を問わない書き方は `CASE WHEN v < lo THEN lo WHEN v > hi THEN hi ELSE v END`（sqlite / duckdb で確認。`NULL` は `NULL` のまま）
- 範囲内かの判定だけなら `v BETWEEN lo AND hi`
- 上限だけなら `MIN(v, hi)` / `LEAST(v, hi)`、下限だけなら `MAX(v, lo)` / `GREATEST(v, lo)`

## Pitfalls

- TypeScript（es-toolkit の `clamp`）は `NaN` を返し、Python は `x` が `NaN` のとき `NaN`。SQL は `NULL` が伝播する（sqlite）か無視される（duckdb）かで、境界の欠損に気付けない
- 引数の数で集計かスカラーかが変わる（sqlite）。`SELECT MAX(v) FROM t` は 1 行の集計、`SELECT MAX(v, 0) FROM t` は行ごと。duckdb は 2 引数の `MAX` が別の集計（上位 n 件）なので、移植すると意味が変わる
- 列に文字列が混ざる（sqlite の型の緩さ）と型順序で比較される。数値列であることを `typeof(v)` で確認するか `CAST(v AS REAL)` する
- `lo > hi` の検証は無い。引数を取り違えても常に `hi` が返るだけで気付きにくい

## Test

`examples/number-clamp_test.py`
