---
id: date-start-of-day
lang: sql
title: 日付の時刻を 0 時に切り捨てる
tags: [日付切り捨て, 0時, 日単位, タイムゾーン, start-of-day, truncate, date-trunc, midnight]
lib: sqlite
fn: DATE
since: "3.0"
verified: 2026-09-17
status: public
---

日時から時刻を落として日付だけ（または当日 0 時）にする。日ごとの集計キーや「今日の範囲」の下限に使う。どのタイムゾーンの 0 時かを先に決める。

## Signature

```sql
DATE(ts)   -- DATETIME(ts, 'start of day')
```

## Usage

```sql
SELECT DATE('2024-02-29 13:45:07'), DATETIME('2024-02-29 13:45:07', 'start of day'),
       DATE('2024-02-29 23:45:07', '+9 hours'), DATE('2024-03-01 08:45:07+09:00');
-- => ('2024-02-29', '2024-02-29 00:00:00', '2024-03-01', '2024-02-29')
--    '+9 hours' で JST の日付、'+09:00' 付き入力は UTC に直してから日付を取る
```

## Contract

- `DATE(ts)` は日付部分の TEXT `YYYY-MM-DD`、`DATETIME(ts, 'start of day')` は `YYYY-MM-DD 00:00:00`。どちらも TEXT
- 冪等。時刻が `00:00:00` の入力や日付だけの入力を渡しても同じ値になる
- 秒未満は切り捨て（`13:45:07.999` → 同じ日）。`23:59:59.999` も同じ日
- UTC 前提。オフセット付きの入力（`+09:00`）は UTC に変換してから日付を取るので、`2024-03-01 08:45:07+09:00` は `2024-02-29`。特定ゾーンの日付が欲しければ `'+9 hours'` のような修飾子で先にずらす（DST が無いゾーン向け）。`'localtime'` は実行環境のタイムゾーンに依存する
- 非 ISO 形式・不正な文字列・`NULL` は `NULL`
- 結果は TEXT なので `ts` との比較は文字列比較になる。辞書順が時系列順になるのは両辺が同じ形（`DATETIME()` を通した UTC の `YYYY-MM-DD HH:MM:SS`）のときだけで、`DATETIME(ts, 'start of day') <= DATETIME(ts)` は常に真だが、`ts` が日付だけ（`'2024-02-29'`）だと `'2024-02-29 00:00:00' <= '2024-02-29'` は偽、オフセット付き（`'2024-03-01 08:45:07+09:00'`）だと左辺は UTC の `2024-02-29 00:00:00` で右辺は生の文字列と、正規化していない側とは噛み合わない。比較する列は保存時に `DATETIME()` で正規化しておくか、比較の両辺に `DATETIME()` を通す
- 修飾子は左から順に適用される。`'start of day', '+1 day'` で翌日 0 時、`'start of day', '+1 day', '-1 second'` で当日 `23:59:59`。`'start of month'` / `'start of year'` もある
- duckdb: `DATE_TRUNC('day', ts)` は TIMESTAMP（`2024-02-29 00:00:00`）、`ts::DATE` は DATE。`DATE_TRUNC('day', DATE '...')` も TIMESTAMP を返す（1.5.0 で DATE から TIMESTAMP に変わった。1.4.4 では DATE。テストは duckdb 1.5 以上を前提にする）。TIMESTAMPTZ は `TimeZone` 設定のローカル日で切られ結果も TIMESTAMPTZ になるので、UTC の日付なら `ts AT TIME ZONE 'UTC'` で TIMESTAMP にしてから切る（`TimeZone` 設定と `AT TIME ZONE` は ICU 拡張が前提。同梱されないビルドでは `INSTALL icu; LOAD icu;` が要る）。文字列リテラルはそのまま渡せず `::TIMESTAMP` が要る。`'day'` / `'days'` / `'DAY'` はどれも可

## Alternatives

- duckdb / PostgreSQL: `DATE_TRUNC('day', ts)`（timestamp）/ `ts::date`（date）。MySQL: `DATE(ts)`。BigQuery: `TIMESTAMP_TRUNC(ts, DAY, 'Asia/Tokyo')` / `DATE(ts, 'Asia/Tokyo')` とタイムゾーンを引数で指定すると書かれる
- 日付キーで集計するなら `GROUP BY DATE(ts)`
- 「その日の範囲」は `ts >= DATE(x) AND ts < DATE(x, '+1 day')`（`ts` が `YYYY-MM-DD HH:MM:SS` 形式の UTC TEXT である前提。オフセット付きの列なら `DATETIME(ts)` を通す）。`23:59:59` を上限にすると秒未満の値が漏れる
- 時刻部分だけが欲しいなら `TIME(ts)`

## Pitfalls

- TypeScript（date-fns の `startOfDay`）は実行環境のローカルタイムゾーンの 0 時、Python は `tzinfo` に従う。sqlite は UTC 固定なので、JST の「今日」を出すには `'+9 hours'` を明示する。アプリと DB で日付キーが 1 日ずれる典型的な原因
- sqlite の `'localtime'` は DB サーバー / 実行環境のタイムゾーン設定に依存し、テストと本番で結果が変わり得る。固定オフセットの修飾子か、アプリ側で変換した値を渡す
- duckdb の `DATE_TRUNC` は TIMESTAMP、`::DATE` は DATE と型が違う。`= DATE '2024-02-29'` の比較はどちらでも真になるが、`GROUP BY` のキーや出力の見た目が変わる
- `DATE(ts)` の結果は文字列。数値や日付型と比較するとき暗黙変換されない（sqlite は型が緩いので気付きにくい）

## Test

`examples/date-start-of-day_test.py`
