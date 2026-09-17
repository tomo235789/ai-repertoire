---
id: date-diff-days
lang: sql
title: 2 つの日付の暦日差を求める
tags: [日付差, 日数, 経過日数, ユリウス日, diff-days, date-diff, julianday, calendar-days]
lib: sqlite
fn: JULIANDAY
since: "3.0"
verified: 2026-09-17
status: public
---

2 つの日付の間の日数を返す。残日数や経過日数の計算に使う。時刻を含む値は先に `DATE()` で日付に落とさないと暦日差にならない。

## Signature

```sql
CAST(JULIANDAY(d2) - JULIANDAY(d1) AS INTEGER)
```

## Usage

```sql
SELECT CAST(JULIANDAY('2024-03-01') - JULIANDAY('2024-02-28') AS INTEGER),
       CAST(JULIANDAY('2024-02-28') - JULIANDAY('2024-03-01') AS INTEGER),
       CAST(JULIANDAY(DATE('2024-03-01 00:30:00')) - JULIANDAY(DATE('2024-02-29 23:00:00')) AS INTEGER),
       JULIANDAY('2024-03-01 00:30:00') - JULIANDAY('2024-02-29 23:00:00');
-- => (2, -2, 1, 0.0625)   -- 時刻を含めたままだと小数（1.5 時間 = 0.0625 日）
```

## Contract

- `JULIANDAY(x)` はユリウス日を REAL で返す（起点は UTC 正午）。差はそのまま日数で、時刻の無い日付同士なら整数値の REAL（`2.0`）
- 符号は `d2 - d1`。後の日付から前の日付を引くと正、逆なら負、同じ日なら `0`
- 時刻を含む値は `DATE(x)` で日付部分にしてから引く。落とさないと `23:00` → 翌 `00:30` の差が `0.0625` になり、`CAST AS INTEGER` で `0` になる（暦日差は `1`）
- `CAST(... AS INTEGER)` はゼロ方向の切り捨て。ミリ秒のずれ（`'2024-02-28 00:00:00.001'`）で差が `1.99999…` になると `1` に落ちる。`DATE()` を挟めば `2`
- タイムゾーンや DST の影響は無い（sqlite は UTC 前提）。オフセット付きの入力は UTC に変換されてから扱われる（`'2024-03-01T00:00:00+09:00'` は 02-29 15:00 UTC なので `DATE()` は `2024-02-29`）
- 非 ISO 形式・不正な文字列・`NULL` は `NULL`
- 3.38 以降は `(UNIXEPOCH(d2) - UNIXEPOCH(d1)) / 86400` でも書ける（整数除算で 0 方向の切り捨て）
- duckdb: `DATE_DIFF('day', d1, d2)` は BIGINT で **引数順は (開始, 終了)**（`d2 - d1`）。TIMESTAMP を渡すと「日付の境界をまたいだ回数」になる（`23:00` → 翌 `00:30` で `1`、`12:00` → 翌 `11:59:59` でも `1`）。丸 24 時間の数なら `DATE_SUB('day', t1, t2)`（→ `0`）。`DATE '..' - DATE '..'` は整数の日数、TIMESTAMP 同士の引き算は INTERVAL

## Alternatives

- duckdb: `DATE_DIFF('day', d1, d2)` / `DATEDIFF('day', d1, d2)`（同じ）/ `d2 - d1`（DATE 同士）
- PostgreSQL: `d2 - d1`（date 同士は integer）、timestamp は `ts2::date - ts1::date` と書く。MySQL: `DATEDIFF(d2, d1)`（日付部分だけで比較）。BigQuery: `DATE_DIFF(d2, d1, DAY)`（duckdb と引数順が逆）
- 実時間の経過（時刻込み）は `(JULIANDAY(t2) - JULIANDAY(t1)) * 86400` 秒、`* 24` 時間
- 同じ日かの判定だけなら `DATE(a) = DATE(b)`
- 加算は date-add-days

## Pitfalls

- TypeScript（date-fns の `differenceInCalendarDays`）に相当するのは `DATE()` を挟んだ形。`differenceInDays`（丸 24 時間の数、ゼロ方向）に相当するのは時刻込みの `CAST(JULIANDAY(t2) - JULIANDAY(t1) AS INTEGER)`
- Python の `(a - b).days` は −∞ 方向の丸め、sqlite の `CAST AS INTEGER` はゼロ方向。負の小数差で 1 日ずれる（`-0.9` は Python で `-1`、sqlite で `0`）
- 引数の順序が方言でばらばら（duckdb は `(開始, 終了)`、BigQuery / MySQL は `(終了, 開始)`）。移植時に符号が反転する
- 営業日数の計算には別の道具（カレンダーテーブルとの結合）が要る

## Test

`examples/date-diff-days_test.py`
