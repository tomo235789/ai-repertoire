---
id: number-sum-by
lang: sql
title: 配列の各要素から取り出した数値を合計する
tags: [合計, 集計, 総和, NULL値, sum, total, aggregate, coalesce]
lib: sqlite
fn: SUM
since: "3.0"
verified: 2026-09-17
status: public
---

列の値を合計する。`NULL` は無視されるが、該当行が無いと `0` ではなく `NULL` が返る点と、整数のオーバーフローの挙動が方言で違う。

## Signature

```sql
SUM(col)
```

## Usage

```sql
WITH t(qty) AS (VALUES (1), (2), (NULL), (3))
SELECT SUM(qty) AS total, COALESCE(SUM(qty), 0) AS total_or_zero FROM t;
-- => (6, 6)   -- NULL は無視

WITH t(qty) AS (VALUES (1), (2), (NULL), (3))
SELECT SUM(qty), COALESCE(SUM(qty), 0) FROM t WHERE qty > 100;
-- => (NULL, 0)   -- 該当 0 行なら NULL
```

## Contract

- `NULL` の値は無視する。値がすべて `NULL`、または行が 0 件なら結果は `NULL`（`0` ではない）。`0` が欲しければ `COALESCE(SUM(v), 0)`。sqlite には常に REAL を返して空なら `0.0` になる `TOTAL(v)` もある（duckdb には無い）
- 返り値の型: sqlite は整数だけなら INTEGER、実数が混ざると REAL。duckdb は整数列なら HUGEINT（128 ビット）、DECIMAL 列なら DECIMAL(38, s)、DOUBLE 列なら DOUBLE
- オーバーフロー: sqlite は合計が 64 ビットを超えると `integer overflow` エラー（`TOTAL` は REAL に丸めてエラーにしない）。duckdb は HUGEINT に広がるので BIGINT の最大値 + 1 も計算でき、HUGEINT の範囲を超えたときだけエラー
- 文字列: sqlite は数値に変換できるテキストは変換し、できないものは `0` として足す（`1, '2', 'x'` の合計は `3.0`）。duckdb は VARCHAR 列に `SUM` を書くと Binder Error
- 実数の合計: sqlite は 3.43 以降の補正付き加算で `0.1 + 0.2 + 0.3` が `0.6`、`0.1` を 10 回足して `1.0`（3.43.2 / 3.45.1 / 3.53.4 で確認。3.37.2 では素朴な加算でどちらも一致しない）。duckdb の DOUBLE は素朴な加算で `0.6000000000000001`、DECIMAL なら `0.6`。版で最下位桁が変わるので比較は許容誤差付きで行う
- `GROUP BY` と組み合わせるとグループごとの合計。`NULL` だけのグループは `NULL`

## Alternatives

- PostgreSQL: `SUM(integer)` は `bigint`、`SUM(bigint)` は `numeric` を返すと書かれる。MySQL: 整数は DECIMAL、浮動小数は DOUBLE。BigQuery: `SUM(INT64)` は INT64 でオーバーフローはエラーと書かれる
- 条件付きの合計は `SUM(v) FILTER (WHERE cond)`（collection-partition）
- 累積和は `SUM(v) OVER (ORDER BY ...)`（collection-sliding-window）
- 平均は `AVG`（number-mean）
- 式の合計は `SUM(price * qty)` のように式をそのまま書く。行ごとに `NULL` になる式は行ごと無視される

## Pitfalls

- TypeScript の `sumBy([])` / Python の `sum([])` は `0` だが、SQL は `NULL`。API のレスポンスに `null` が混ざったり、`NULL + 1` が `NULL` になったりする。`COALESCE` を付ける
- Python は `None` が混ざると `TypeError` で止まるが、SQL は黙って無視する。欠損を検出したいなら `COUNT(*) - COUNT(v)` を別途出す
- sqlite の TEXT 列に対する `SUM` は変換できない値を `0` として静かに足す。型が緩い列は `typeof(v)` で確認する
- 金額など誤差を許容できない値は整数（最小単位）か DECIMAL で持つ。DOUBLE 列の `SUM` は加算順で最下位ビットが変わり得る

## Test

`examples/number-sum-by_test.py`
