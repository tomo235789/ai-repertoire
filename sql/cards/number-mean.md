---
id: number-mean
lang: sql
title: 数値配列の平均を求める
tags: [平均, 相加平均, 集計, NULL値, mean, average, avg, aggregate]
lib: sqlite
fn: AVG
since: "3.0"
verified: 2026-09-17
status: public
---

列の値の平均を返す。`NULL` は分子にも分母にも入らず、整数列でも結果は実数になる。

## Signature

```sql
AVG(col)
```

## Usage

```sql
WITH t(v) AS (VALUES (1), (2), (NULL), (4))
SELECT AVG(v), SUM(v) * 1.0 / COUNT(*), COUNT(v), COUNT(*) FROM t;
-- => (2.3333333333333335, 1.75, 3, 4)   -- AVG の分母は COUNT(v)=3、COUNT(*)=4 は NULL 行も数える
```

## Contract

- `NULL` の値は無視する。分子（合計）にも分母（件数）にも入らない。`NULL` を `0` として平均したいなら `AVG(COALESCE(v, 0))`
- 行が 0 件、または値がすべて `NULL` なら `NULL`（`0` でもエラーでもない）
- 整数列でも実数を返す。sqlite は REAL（`AVG` of `1, 2` は `1.5`）、duckdb は DOUBLE（DECIMAL 列でも DOUBLE）
- `SUM(v) / COUNT(v)` と書くと sqlite では整数同士の除算になり切り捨てられる（`1, 2` → `1`）。duckdb の `/` は常に実数除算（`1.5`）で、整数除算は `//`
- 実数の表現誤差: `0.1, 0.2, 0.3` の平均は sqlite で `0.19999999999999998`（3.53 で確認。最下位桁は版の加算方式で変わり得るので、比較は許容誤差付きで行う）、duckdb は DECIMAL リテラルなら `0.2`、DOUBLE 列なら `0.20000000000000004`
- 文字列: sqlite は変換できない文字列を `0` として数える（`AVG` of `1, 'x'` は `0.5`）。duckdb は VARCHAR 列で Binder Error
- `GROUP BY` と組み合わせるとグループごとの平均

## Alternatives

- PostgreSQL: `AVG(integer)` は `numeric` を返すと書かれる。MySQL: DECIMAL / DOUBLE。BigQuery: `AVG(INT64)` は FLOAT64
- 中央値は duckdb の `MEDIAN(v)` / `QUANTILE_CONT(v, 0.5)`。sqlite は 3.51.0 以降 percentile 拡張が amalgamation に含まれるが既定では無効で、`SQLITE_ENABLE_PERCENTILE` 付きでビルドされた版だけ `MEDIAN(v)` が使える（手元の 3.53.4 は有効。素のビルドの 3.45.1 は `no such function: MEDIAN`）。`PRAGMA compile_options` に `ENABLE_PERCENTILE` があるかで判別し、無ければ拡張を読み込むかアプリ側で計算する
- 加重平均は `SUM(v * w) / SUM(w)`（sqlite では `* 1.0` で実数にする）
- 移動平均は `AVG(v) OVER (ORDER BY ... ROWS BETWEEN n PRECEDING AND CURRENT ROW)`（collection-sliding-window）
- 条件付き平均は `AVG(v) FILTER (WHERE cond)`（collection-partition）

## Pitfalls

- Python の `statistics.fmean([])` は例外、TypeScript（es-toolkit の `mean([])`）は `NaN`、SQL は `NULL`。空の扱いが 3 者で違う
- Python は `None` が混ざると `TypeError` だが SQL は黙って除外する。「未回答を 0 点として平均」なのか「未回答を除いて平均」なのかを `COALESCE` の有無で明示する
- `SUM / COUNT` で自前計算すると sqlite は整数除算になる。`AVG` を使うか `* 1.0` を挟む
- `COUNT(*)` で割ると `NULL` の行も分母に入り `AVG` と一致しない

## Test

`examples/number-mean_test.py`
