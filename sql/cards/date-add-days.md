---
id: date-add-days
lang: sql
title: 日付に日数を加算する
tags: [日付加算, 日数, 月末, 修飾子, add-days, date-arithmetic, interval, modifier]
lib: sqlite
fn: DATE
since: "3.0"
verified: 2026-09-17
status: public
---

日付に `N` 日を足した日付を返す。期限の計算や期間の生成に使う。sqlite は修飾子文字列、duckdb は `INTERVAL` で書く。

## Signature

```sql
DATE(d, '+N days')
```

## Usage

```sql
SELECT DATE('2024-02-28', '+1 day'), DATE('2024-02-29', '+1 day'), DATE('2024-12-31', '+1 day'),
       DATE('2024-02-29', '-1 day'), DATE('2024-01-31', '+1 month');
-- => ('2024-02-29', '2024-03-01', '2025-01-01', '2024-02-28', '2024-03-02')
--    '+1 month' は「2 月 31 日」を正規化して 3 月 2 日になる
```

## Contract

- 修飾子は `'+N days'` / `'-N days'`（`day` / `days` どちらでも可、符号無しの `'1 day'` も加算）。`'+1day'`（空白無し）や `'+ 1 day'`（符号と数の間に空白）は `NULL`。`'+-1 day'` も `NULL`
- 月末・年末・うるう年の繰り越しはカレンダーどおり（`2024-02-29` + 1 → `2024-03-01`、+ 365 → `2025-02-28`）
- 返り値は TEXT の `YYYY-MM-DD`。時刻付きの入力（`'2024-02-29 23:30:00'`）でも日付だけになる。時刻を保つなら `DATETIME(ts, '+1 day')`
- 小数の日数 `'+1.5 days'` は 36 時間（`DATETIME` なら `2024-03-01 12:00:00`、`DATE` なら `2024-03-01`）
- `'+1 month'` / `'+1 year'` は月・年の数字だけ変えてから正規化する（`2024-01-31` + 1 month → 2 月 31 日 → `2024-03-02`、`2024-02-29` + 1 year → `2025-03-01`）。3.46 以降は `'floor'` 修飾子を後ろに付けると月末に丸める（→ `2024-02-29`）
- 修飾子は複数書け、左から順に適用される（`'+1 month', '-1 day'`）
- 非 ISO 形式（`'2024/02/29'`）、不正な文字列、`NULL` は `NULL`。無い日付 `'2024-02-30'` は正規化される（+ 1 day → `2024-03-02`）
- 範囲は `0000-01-01` 〜 `9999-12-31`。`9999-12-31` + 1 day は `NULL`
- `N` を列から作るときは `'+' || n || ' days'` だと負数で `'+-3 days'` → `NULL` になる。`printf('%+d days', n)` で符号込みにする
- duckdb: `DATE '2024-02-29' + INTERVAL 1 DAY` は **TIMESTAMP** を返す（`2024-03-01 00:00:00`）。DATE のままにするなら `d + 1`（整数の加算）か `(d + INTERVAL 1 DAY)::DATE`。文字列リテラルにそのまま `+ INTERVAL` はできない（`DATE` 型が要る）。`INTERVAL 1.5 DAY` は構文エラーで、`INTERVAL '1.5 days'` なら 36 時間。`INTERVAL 1 MONTH` は月末にクランプする（`2024-01-31` + 1 month → `2024-02-29`。sqlite と逆）。無い日付は Conversion Error、`9999-12-31` + 1 は `10000-01-01`

## Alternatives

- duckdb: `d + INTERVAL 1 DAY`（TIMESTAMP）、`d + 1`（DATE）、`DATE_ADD(d, INTERVAL 1 DAY)`。日数が列なら `d + INTERVAL (n) DAY` か `d + to_days(n)`
- PostgreSQL: `d + 1`（date + integer は date）/ `d + INTERVAL '1 day'`（timestamp）と書く。MySQL: `DATE_ADD(d, INTERVAL 1 DAY)` / `d + INTERVAL 1 DAY`。BigQuery: `DATE_ADD(d, INTERVAL 1 DAY)`
- 週は `'+7 days'`。月末を狙うなら sqlite は `DATE(d, 'start of month', '+2 months', '-1 day')`
- 逆演算（日数差）は date-diff-days

## Pitfalls

- TypeScript（date-fns の `addDays(d, 1.5)`）は小数を切り捨てて 1 日だが、Python の `timedelta(days=1.5)` と sqlite の `'+1.5 days'` は 36 時間
- `'+1 month'` の月末処理は sqlite（正規化して繰り越し）と duckdb / Python の `relativedelta`（月末にクランプ）で結果が違う。`2024-01-31` + 1 month が `03-02` か `02-29` か
- sqlite は形式が違う文字列に対して静かに `NULL` を返す。列に `'2024/02/29'` が混ざっていると加算結果が消える
- duckdb は `INTERVAL` を足すと型が DATE から TIMESTAMP に変わる。`= DATE '2024-03-01'` の比較は通るが、表示や `GROUP BY` のキーが変わる

## Test

`examples/date-add-days_test.py`
