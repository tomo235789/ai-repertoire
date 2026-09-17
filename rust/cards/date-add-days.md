---
id: date-add-days
lang: rust
title: 日付に日数を加算する
tags: [日付加算, 日数, 減算, 月末, うるう年, add-days, plus, date-math]
lib: chrono
fn: DateTime::checked_add_days
since: "0.4"
verified: 2026-09-17
status: public
---

`DateTime` / `NaiveDate` に `Days::new(n)` を足して新しい値を得る（減算は `checked_sub_days`）。期限日や有効期間の計算に使う。壁時計の日付を進めるので `+ Duration::days(1)`（経過時間）とは DST で結果が変わる。

## Signature

```rust
pub fn checked_add_days(self, days: Days) -> Option<Self>
```

## Usage

```rust
use chrono::{Days, NaiveDate, TimeZone, Utc};

let d = Utc.with_ymd_and_hms(2024, 2, 29, 13, 45, 7).unwrap();
d.checked_add_days(Days::new(1));   // => Some(2024-03-01T13:45:07Z)
d.checked_add_days(Days::new(365)); // => Some(2025-02-28T13:45:07Z)
d.checked_sub_days(Days::new(60));  // => Some(2023-12-31T13:45:07Z)
NaiveDate::from_ymd_opt(2024, 2, 29).unwrap().checked_add_days(Days::new(1)); // => Some(2024-03-01)
```

## Contract

- `DateTime` は `Copy` なので入力は変わらず、新しい値を `Some` で返す。`Days::new(0)` は同じ値
- 月末・年末・うるう年の繰り越しはカレンダーどおり（`2024-02-29` + 1 → `2024-03-01`、+365 → `2025-02-28`）
- 時・分・秒・ナノ秒とオフセットはそのまま保たれる。`Utc` / `FixedOffset` には DST が無いので経過時間はちょうど 24 時間 × 日数で、`+ Duration::days(n)` と同じ結果
- `Days` は `u64` で負数は渡せない。減算は `checked_sub_days`
- 範囲外（`DateTime::<Utc>::MAX_UTC` や `NaiveDate::MAX` を超える、`Days::new(u64::MAX)` など）は `None`。panic しない
- `NaiveDate` / `NaiveDateTime` にも同じ `checked_add_days` / `checked_sub_days` がある

## Alternatives

- `d + Duration::days(1)`（`TimeDelta`）は **経過時間** で足す。`Utc` / `FixedOffset` では同じ結果だが、範囲外は panic（`checked_add_signed` なら `None`）。`Duration::days(i64::MAX)` のような大きすぎる値も panic（`try_days` なら `None`）
- 時間単位で足すなら `Duration::hours(36)`。`NaiveDate + Duration` は日未満を切り捨てる（`+ 23h` は同じ日、`+ 36h` は翌日）
- 月・年は `checked_add_months(Months::new(1))`。月末は月の最終日にクランプ（`2024-01-31` + 1 か月 → `2024-02-29`、`2024-02-29` + 12 か月 → `2025-02-28`）
- 週は `Duration::weeks(1)`。翌日だけなら `NaiveDate::succ_opt()`
- 経過日数を求めるのは date-diff-days

## Pitfalls

- DST のあるタイムゾーン（`TZ=America/New_York` の `Local`）では `checked_add_days` は壁時計を保つ（3/9 12:00 の 1 日後は 3/10 12:00 で経過 23 時間）が、`+ Duration::days(1)` は経過時間を保つ（3/10 13:00）。進めた先の壁時計が存在しない（切替で飛ぶ 2:30）と `checked_add_days` は `None`、`+ Duration` は `03:30` を返す
- TypeScript（date-fns の `addDays`）と Python の `timedelta(days=1)` は壁時計を保つ点で `checked_add_days` と同じ。Python は存在しない時刻に着地しても例外を出さないが、chrono は `None`
- Python の `timedelta(days=1.5)` は 36 時間だが、`Days::new` は整数のみ。時間で足すなら `Duration::hours`
- 返り値は `Option`。ユーザー入力の日数を足すときは `unwrap` せず `None` を扱う

## Test

`tests/date_add_days.rs`
