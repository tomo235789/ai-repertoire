---
id: date-add-days
lang: csharp
title: 日付に日数を加算する
tags: [日付加算, 日数, 減算, 月末, うるう年, add-days, plus, date-math]
lib: stdlib
fn: DateTime.AddDays
since: "6.0"
verified: 2026-09-17
status: public
---

`DateTime` に日数を足した新しい値を返す（負数で減算）。期限日や有効期間の計算に使う。

## Signature

```csharp
public DateTime AddDays(double value)
```

## Usage

```csharp
using System;

var d = new DateTime(2024, 2, 29, 13, 45, 0);
d.AddDays(1);   // => 2024-03-01 13:45
d.AddDays(-1);  // => 2024-02-28 13:45
d.AddDays(366); // => 2025-03-01 13:45
d.AddDays(1.5); // => 2024-03-02 01:45（小数は時間に換算。1.5 日 = 36 時間）
d;              // 変わらない（struct）
```

## Contract

- 入力を変更せず新しい値を返す（`DateTime` は不変の struct）
- 月末・年末・うるう年の繰り越しはカレンダーどおり（`2024-02-29` + 1 → `2024-03-01`、+ 365 → `2025-02-28`）
- 時・分・秒・ティックと `Kind` は保たれる
- `value` は `double`。小数は **時間に換算** され、`AddDays(1.5)` は 36 時間、`AddDays(-1.5)` は −36 時間進める。`AddDays(0.5)` は `TimeSpan.FromDays(0.5)` を足すのと同じ
- 壁時計の値をそのまま進める。`Kind` に関係なくタイムゾーンや DST を考慮しないので、`TimeZoneInfo` で UTC に直すと DST 切替をまたぐ日は実時間 23 時間または 25 時間になる
- 結果が `DateTime.MinValue`〜`MaxValue` の外に出ると `ArgumentOutOfRangeException`。`±∞` や桁の大きすぎる値も同じ例外
- `DateTimeOffset.AddDays` はオフセットを固定したまま進めるので、実時間は常に 24 時間 × 日数

## Alternatives

- `d + TimeSpan.FromDays(1.5)` でも同じ。減算は `d - TimeSpan.FromDays(1)` か負数を渡す
- 月・年は `AddMonths` / `AddYears`（月末を月の最終日にクランプする。`2024-01-31` + 1 か月 → `2024-02-29`）
- 時刻を持たない日付は `DateOnly.AddDays(int)`（整数のみ）
- 特定のタイムゾーンで「翌日の同じ時刻」が欲しければ、そのゾーンの壁時計で足してから `TimeZoneInfo.ConvertTimeToUtc`
- 経過日数を求めるのは `date-diff-days`

## Pitfalls

- TypeScript（date-fns の `addDays`）は小数を切り捨てて `addDays(d, 1.5)` が 1 日だが、`AddDays(1.5)` は 36 時間。Python の `timedelta(days=1.5)` と同じ意味論。日数は整数で渡すか、意図して時間単位で足す
- `d.AddDays(1);` と書いて戻り値を捨てると何も起きない。必ず戻り値を使う
- `AddDays(30)` は「1 か月」ではない。月単位は `AddMonths`
- `Kind = Local` でも DST は補正されない。「ちょうど 24 時間後」が欲しければ `DateTimeOffset` か UTC で計算する

## Test

`examples/DateAddDaysTests.cs`
