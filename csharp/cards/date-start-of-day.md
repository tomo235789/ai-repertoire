---
id: date-start-of-day
lang: csharp
title: 日付の時刻を 0 時に切り捨てる
tags: [日付の切り捨て, 0時, 日の始まり, 時刻除去, start-of-day, midnight, truncate-time, floor]
lib: stdlib
fn: DateTime.Date
since: "6.0"
verified: 2026-09-17
status: public
---

`DateTime` の時刻部分を `00:00:00` にした新しい値を返す。日単位のキーやグルーピング、範囲検索の下限に使う。

## Signature

```csharp
public DateTime Date { get; }
```

## Usage

```csharp
using System;

var d = new DateTime(2024, 2, 29, 13, 45, 7, 123, DateTimeKind.Local);
d.Date; // => 2024-02-29 00:00:00.000（Kind は Local のまま）
d.Hour; // => 13（元は変わらない）
var o = new DateTimeOffset(2024, 2, 29, 13, 45, 7, TimeSpan.FromHours(9));
new DateTimeOffset(o.Date, o.Offset); // => 2024-02-29T00:00:00+09:00（Date だけだとオフセットが落ちる）
```

## Contract

- 日付部分はそのまま、時刻を `00:00:00.0000000` にする。ミリ秒以下のティックも 0 になる
- `Kind` を保つ（`Local` → `Local`、`Utc` → `Utc`、`Unspecified` → `Unspecified`）
- 入力を変更せず新しい値を返す（`DateTime` は不変の struct）。冪等で、`d.Date.Date == d.Date`
- 壁時計の日付で丸めるので、実行環境のタイムゾーンに依存しない。`Kind = Utc` なら UTC の 0 時、`Unspecified` なら「どこのゾーンでもない 0 時」
- `DateTimeOffset.Date` は **`Kind = Unspecified` の `DateTime`** を返し、オフセット情報が落ちる。日付はそのオフセットでのローカル日付（`o.UtcDateTime.Date` とは 1 日ずれ得る）
- 例外は投げない。`DateTime.MinValue.Date` は `DateTime.MinValue`

## Alternatives

- 時刻の無い型で持つなら `DateOnly.FromDateTime(d)`
- `DateTimeOffset` でオフセットを保ったまま 0 時にするなら `new DateTimeOffset(o.Date, o.Offset)`
- 特定のタイムゾーンでの 0 時が欲しいなら `TimeZoneInfo.ConvertTime(o, tz).Date` か `TimeZoneInfo.ConvertTimeFromUtc(utc, tz).Date`
- 日の終わりは `d.Date.AddDays(1)` を上限に `<` で比較する（`23:59:59.9999999` を作らない）
- 今日の 0 時は `DateTime.Today`（`Kind = Local`）

## Pitfalls

- TypeScript（date-fns の `startOfDay`）は実行環境のローカルタイムゾーンで丸めるが、C# は `Kind` に関係なく壁時計で丸める。UTC で持っている値を `.Date` にすると UTC の日付になり、ローカルの「今日」とは異なり得る。Python の `replace(hour=0, ...)` と同じで、先にゾーン変換してから丸める
- `DateTimeOffset.Date` はオフセットを捨てて `Unspecified` にする。そのまま `"o"` で書き出すと `Z` もオフセットも付かず、受け手が解釈できない
- `Kind = Unspecified` の値を DB や JSON に出すと、読み手がローカルか UTC か決められない。日付キーとして保存するなら `DateOnly` か UTC に揃える
- 日の終わりを `AddTicks(-1)` で作ると `>=` / `<=` の境界で漏れやすい。翌日 0 時未満で判定する

## Test

`examples/DateStartOfDayTests.cs`
