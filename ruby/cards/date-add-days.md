---
id: date-add-days
lang: ruby
title: 日付に日数を加算する
tags: [日付加算, 日数, 減算, 月末, うるう年, add-days, plus, next-day, date-math]
lib: stdlib
fn: Date#+
since: "1.9"
verified: 2026-09-17
status: public
---

`Date` に日数を足した新しい `Date` を返す（負数で減算）。期限日や有効期間の計算に使う。`require "date"` が要る。

## Signature

```ruby
date + other -> new_date
```

## Usage

```ruby
require "date"

d = Date.new(2024, 2, 29)
d + 1    # => #<Date: 2024-03-01>
d - 1    # => #<Date: 2024-02-28>
d + 366  # => #<Date: 2025-03-01>
d.next_day(3)  # => #<Date: 2024-03-03>
d        # 変わらない
```

## Contract

- 入力を変更せず新しいオブジェクトを返す（`+ 0` でも別インスタンス）。`Date` は不変
- 月末・年末・うるう年の繰り越しはカレンダーどおり（`2024-02-29` + 1 → `2024-03-01`、+ 365 → `2025-02-28`、`2024-12-31` + 1 → `2025-01-01`）
- `Rational` や `Float` を足すと日未満の端数を **内部の時刻として保持する**。`Date.new(2024, 2, 29) + 1.5` は `to_s` では `"2024-03-01"` だが `day_fraction` が `1/2` になり、`Date.new(2024, 3, 1)` と `==` で等しくならない（`===` は同じ日なら真）。さらに `+ 0.5` すると `2024-03-02` になる。`DateTime` に足すと時刻がそのまま進む（`2024-02-29 13:45` + `1.5` → `2024-03-02 01:45`）。日数は整数で渡す
- 数値以外（`String`、`nil`、`Date`）を足すと `TypeError`（`expected numeric`）。`Float::INFINITY` / `Float::NAN` は `FloatDomainError`
- `Date - Date` は日数の `Rational`（`Date.new(2024, 2, 29) - Date.new(2024, 2, 1)` は `(28/1)`）。`to_i` で整数にする
- 暦（`start`）は保たれる。既定の `Date::ITALY` では `1582-10-04` + 1 が `1582-10-15` になる（グレゴリオ暦への切替）
- 純粋関数。例外は上記のみ

## Alternatives

- `next_day(n)` / `prev_day(n)` は `+ n` / `- n` と同じ（`n` の既定は 1）。`succ` / `next` は `+ 1`
- 月・年は `>>` / `<<`（`next_month` / `prev_month` / `next_year`）。月末は月の最終日にクランプする（`Date.new(2024, 1, 31) >> 1` は `2024-02-29`、`Date.new(2024, 2, 29) >> 12` は `2025-02-28`）
- 経過日数を求めるのは date-diff-days
- 日付の範囲は `(d..d + 2).to_a` か `d.step(d + 2)` で列挙できる

## Pitfalls

- `Time` に `+ 1` すると **1 秒** 進む。日を足すなら `t + 86400` か、`t.to_date + 1` で `Date` にしてから足す（`Time` の `+ 86400` は DST 切替をまたぐと壁時計の時刻が 1 時間ずれる）
- Python の `date + timedelta(days=1.5)` は `.days` だけを使って 1 日進め、TypeScript（date-fns）の `addDays(d, 1.5)` はゼロ方向に切り捨てて 1 日。Ruby の `Date + 1.5` は端数を保持したまま `Date` を返すので、比較で食い違う
- `Date + Date` は `TypeError`。差を取るなら `-`
- 月・年を日数で足そうとしない（`+ 30` は「1 か月」ではない）。`>>` を使う

## Test

`examples/date-add-days_test.rb`
