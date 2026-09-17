---
id: date-add-days
lang: go
title: 日付に日数を加算する
tags: [日付加算, 日数, 減算, 月末, うるう年, add-days, plus, date-math]
lib: stdlib
fn: time.Time.AddDate
since: "1.0"
verified: 2026-09-17
status: public
---

`time.Time` に日数を足した新しい値を返す（負数で減算）。期限日や有効期間の計算に使う。

## Signature

```go
func (t Time) AddDate(years int, months int, days int) Time
```

## Usage

```go
import "time"

loc, _ := time.LoadLocation("Asia/Tokyo")
d := time.Date(2024, 2, 29, 13, 45, 0, 0, loc)
d.AddDate(0, 0, 1)   // => 2024-03-01 13:45:00 +0900 JST
d.AddDate(0, 0, -1)  // => 2024-02-28 13:45:00 +0900 JST
d.AddDate(0, 0, 366) // => 2025-03-01 13:45:00 +0900 JST
d                    // 変わらない
```

## Contract

- `time.Time` は値型。元の値は変わらず、新しい値を返す（`AddDate(0, 0, 0)` は `Equal` な値）
- 月末・年末・うるう年の繰り越しはカレンダーどおり（`2024-02-29` + 1 → `2024-03-01`、+365 → `2025-02-28`、`2024-12-31` + 1 → `2025-01-01`）
- `t` の Location の壁時計で日付を進めるので、時・分・秒・ナノ秒は保たれる。DST 切替をまたぐと `Sub` で測った経過時間は 23 時間や 25 時間になる（`America/New_York` の 2024-03-09 12:00 + 1 日 → 03-10 12:00 EDT、差は 23h）
- `time.Date` と同じ正規化をするので、月の加算で存在しない日付になると翌月へ繰り越す（`2023-01-31` + 1 か月 → `2023-03-03`、うるう年の `2024-01-31` + 1 か月 → `2024-03-02`、`2024-02-29` + 1 年 → `2025-03-01`）。月末へのクランプはしない
- DST で存在しない時刻に着地しても panic せず、別の時刻にずれる。どちらのオフセットで解釈するかは `time.Date` と同じく **未規定**（現在の実装では NY の `2024-03-09 02:30` + 1 日 → `2024-03-10 01:30 EST`。`03:30 EDT` になる可能性もある）
- ゼロ値 `time.Time{}` にも足せる（`0001-01-02 00:00:00 UTC`）

## Alternatives

- 週は `AddDate(0, 0, 7*n)`、月・年は第 1・第 2 引数
- 月末にクランプしたいなら翌月の 0 日を作る（`time.Date(y, m+1, 0, 0, 0, 0, 0, loc)` は `m` 月の末日）
- ちょうど 24 時間 × n の実時間を足すなら `t.Add(time.Duration(n) * 24 * time.Hour)`。壁時計はずれうる
- 経過日数を求めるのはカード date-diff-days（`Sub`）

## Pitfalls

- 月末の扱いが違う。TypeScript（date-fns の `addMonths`）は月末を月の最終日にクランプするが、`AddDate` は繰り越す。1 月 31 日に 1 か月足すと 3 月になる
- Python の `timedelta(days=1.5)` のような小数は渡せない（`int` のみ）
- `Add(24 * time.Hour)` は DST 切替日で壁時計が 1 時間ずれる（NY の 03-09 12:00 + 24h → 03-10 13:00 EDT）。日付を進めたいなら `AddDate`
- `time.Now()` の Location は `Local`。ホストの設定で「1 日後」の絶対時刻が変わるので、日付計算は `time.LoadLocation` で Location を明示する

## Test

`examples/date-add-days_test.go`
