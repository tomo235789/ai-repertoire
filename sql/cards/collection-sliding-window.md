---
id: collection-sliding-window
lang: sql
title: 配列をスライディングウィンドウで走査する
tags: [スライディングウィンドウ, 移動平均, 窓関数, 直近n件, sliding-window, moving-average, window-frame, rolling]
lib: sqlite
fn: OVER (ROWS BETWEEN n PRECEDING AND CURRENT ROW)
since: "3.25"
verified: 2026-09-17
status: public
---

各行について「直前 n 行 + 自分」の窓で集計する。移動平均・直近 n 件の合計に使う。

## Signature

```sql
AGG(col) OVER (ORDER BY sort_col ROWS BETWEEN n PRECEDING AND CURRENT ROW)
```

## Usage

```sql
WITH t(d, v) AS (VALUES (1, 10), (2, 20), (3, 30), (4, 40), (5, 50))
SELECT d, AVG(v) OVER (ORDER BY d ROWS BETWEEN 2 PRECEDING AND CURRENT ROW) AS ma3
FROM t ORDER BY d;
-- => (1, 10.0), (2, 15.0), (3, 20.0), (4, 30.0), (5, 40.0)   -- 先頭 2 行は窓が短い
```

## Contract

- 各行につき、`ORDER BY` 順で直前 `n` 行と自分自身（最大 `n + 1` 行）を集計する。行数ベースで、値の飛びや同値は関係ない
- 先頭では窓が短くなる（1 行、2 行、…）。捨てたり埋めたりしない。`COUNT(*) OVER w` で窓の行数が取れるので、満たない窓を `NULL` にするなら `CASE WHEN COUNT(*) OVER w = 3 THEN AVG(v) OVER w END`（`WINDOW w AS (...)` 句は sqlite 3.25+ / duckdb で書ける）
- `OVER` の `ORDER BY` を省くと窓の並びは不定。必ず書く。`ROWS` の `ORDER BY` に同値があると、同値行のどれが「直前の行」になるかも不定なので、一意になる列を末尾に足す（`ORDER BY d, id`）
- `ROWS` は行数、`RANGE` は `ORDER BY` の値の範囲。キーが数値なら `RANGE BETWEEN 2 PRECEDING AND CURRENT ROW` は「値が `d - 2` 以上 `d` 以下の行」で、同値の行をまとめて含み、値が飛んでいれば行数が減る。日付文字列（`'2024-01-01'`）をキーにすると sqlite はエラーにならず期待と違う窓になる（確認した版では各行が自分だけの窓になった）ので `ORDER BY JULIANDAY(d)` と数値にする。duckdb は VARCHAR キーだと Binder Error、DATE キーなら `INTERVAL` で幅を書く（Alternatives 参照）
- `ORDER BY` だけ書いてフレームを省くと既定は `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`（累積。同値の行は全部含む）
- `NULL` は集計から除かれる（`AVG` の分母にも入らない）。窓内が全部 `NULL` なら `NULL`
- `PARTITION BY` を付けるとグループごとに窓が区切られ、前のグループの行は入らない
- `AVG` は整数列でも実数（sqlite は REAL、duckdb は DOUBLE）。`SUM` / `COUNT` は整数
- 0 行なら 0 行。結果の順序は外側の `ORDER BY` で決める

## Alternatives

- PostgreSQL / MySQL 8.0+ / BigQuery / duckdb は同じ構文
- `ROWS 2 PRECEDING` は `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` の省略形（sqlite / duckdb で確認）
- 前後を含む中心窓は `ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING`。累積和は `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`
- 満たない窓を落とすなら `ROW_NUMBER() OVER (ORDER BY d) >= 3` をサブクエリで絞る（duckdb は `QUALIFY COUNT(*) OVER w = 3`）
- 日付の飛びを考慮して「直近 7 日」にするなら、DATE 列をキーに duckdb は `RANGE BETWEEN INTERVAL 6 DAY PRECEDING AND CURRENT ROW`（`INTERVAL '6 days'` も通る。1.5 で確認）、PostgreSQL は `RANGE BETWEEN INTERVAL '6 days' PRECEDING AND CURRENT ROW` と書く。sqlite は日付文字列を `JULIANDAY(d)` にして `RANGE BETWEEN 6 PRECEDING AND CURRENT ROW`

## Pitfalls

- 末尾・先頭の扱いが 3 通り違う。TypeScript（es-toolkit の `windowed`）は `size` に満たない窓を **捨て**、Python（more-itertools の `windowed`）は `fillvalue` で **埋め**、SQL は短い窓で **集計する**。移動平均の先頭 `n - 1` 行は「短い窓の平均」なので、アプリ側の結果と一致させるなら `COUNT(*) OVER w` で除く
- `ROWS` と `RANGE` の取り違え。`ORDER BY d` の `d` に同値があると `RANGE` は同値行を全部含む。フレームを省略した `SUM(v) OVER (ORDER BY d)` も `RANGE` なので、同じ日の行は同じ累積値になる
- 時系列で欠損日があると `ROWS 6 PRECEDING` は「直前 6 行」であって「直前 6 日」ではない。かといって日付文字列のまま `RANGE 6 PRECEDING` にしても sqlite は黙って違う窓を返す（`JULIANDAY` で数値にする）
- 窓関数は `WHERE` に書けない。結果で絞るならサブクエリ

## Test

`examples/collection-sliding-window_test.py`
