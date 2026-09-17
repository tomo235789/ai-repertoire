---
id: date-diff-days
lang: csharp
title: 2 つの日付の暦日差を求める
tags: [日付差, 日数差, 経過日数, 暦日, diff, days-between, difference, calendar-days]
lib: stdlib
fn: 日付の減算
since: "6.0"
verified: 2026-09-17
status: public
---

時刻を無視して、2 つの日付が暦の上で何日離れているかを返す。残り日数の表示や「同じ日か」の判定に使う。`.Date` で時刻を落としてから引き、`TimeSpan.Days` を読む。

## Signature

```csharp
public static TimeSpan operator -(DateTime d1, DateTime d2)
```

## Usage

```csharp
using System;

var later = new DateTime(2024, 3, 1, 0, 1, 0);      // 2024-03-01 00:01
var earlier = new DateTime(2024, 2, 29, 23, 59, 0); // 2024-02-29 23:59
(later.Date - earlier.Date).Days; // => 1（2 分差でも暦日は 1 日違う）
(earlier.Date - later.Date).Days; // => -1
(later - earlier).Days;           // => 0（時刻込みの経過時間を切り捨て）
(new DateTime(2025, 3, 1) - new DateTime(2024, 3, 1)).Days; // => 365
```

## Contract

- `DateTime - DateTime` は `TimeSpan` を返す。`.Date` で時刻を落としてから引けば `.Days` が暦日差。左辺が後の日付なら正、前なら負、同じ日なら `0`
- `.Date` を付けずに引いた `TimeSpan.Days` は経過時間を 24 時間で割って **ゼロ方向に切り捨て** た値（`-12 時間` → `0`、`36 時間` → `1`）。深夜をまたぐ短い間隔では `0` になる
- `TimeSpan.TotalDays` は小数を含む実時間の日数（`-12 時間` → `-0.5`）
- `Kind` が違っても補正されない。`Utc` の `00:00` から `Local` の `00:00` を引くと `0`（壁時計の値同士の差）
- 入力を変更しない。`DateTime.MaxValue - DateTime.MinValue` でも例外は出ない
- `DateTimeOffset - DateTimeOffset` は UTC に揃えた実時間の差。`DateTimeOffset.Date` はそれぞれのオフセットでのローカル日付（`Kind = Unspecified` の `DateTime`）なので、別オフセット同士を `.Date` で引くとローカル暦日の差になる

## Alternatives

- 時刻を持たない `DateOnly` なら `a.DayNumber - b.DayNumber`。`DateOnly.FromDateTime(dt)` で変換できる
- 「丸 1 日（24 時間）が何回あるか」なら `(later - earlier).Days`、実時間の日数は `(later - earlier).TotalDays`
- 同じ日かだけ知りたいなら `a.Date == b.Date`
- 月・年の暦単位差は標準に無い。`(a.Year - b.Year) * 12 + a.Month - b.Month` で自前計算する

## Pitfalls

- Python の `(a - b).days` は −∞ 方向の丸め（`-12 時間` → `-1`）だが、C# の `TimeSpan.Days` はゼロ方向（`0`）。負の差で 1 日ずれる。TypeScript（date-fns の `differenceInDays`）はゼロ方向で C# と同じ
- `(a - b).Days` を暦日差のつもりで使うと、`00:01` と前日 `23:59` の差が `0` になる。暦日差には必ず `.Date` を付ける
- 別オフセットの `DateTimeOffset` を `.Date` で引くと、瞬間としては前の値が後になり得る（JST `03-01 00:30` と UTC `02-29 20:00` の差は `+1`）。同じ基準で数えるなら `.UtcDateTime.Date` か `ToOffset` で揃える
- `Kind = Local` の値でも DST は考慮されない。壁時計の日付差が欲しいなら問題ないが、実時間が欲しければ `DateTimeOffset` で引く

## Test

`examples/DateDiffDaysTests.cs`
