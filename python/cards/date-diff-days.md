---
id: date-diff-days
lang: python
title: 2 つの日付の暦日差を求める
tags: [日付差, 日数差, 経過日数, 暦日, diff, days-between, difference, calendar-days]
lib: stdlib
fn: date.__sub__
since: "3.0"
verified: 2026-09-17
status: public
---

時刻を捨てて `date` 同士を引き、2 つの日付が暦の上で何日離れているかを求める。残り日数の表示や「同じ日か」の判定に使う。

## Signature

```python
date1 - date2 -> timedelta
```

## Usage

```python
from datetime import date, datetime

later = datetime(2024, 3, 1, 0, 1)      # 2024-03-01 00:01
earlier = datetime(2024, 2, 29, 23, 59)  # 2024-02-29 23:59
(later.date() - earlier.date()).days    # => 1（2 分差でも暦日は 1 日違う）
(earlier.date() - later.date()).days    # => -1
(date(2025, 3, 1) - date(2024, 3, 1)).days  # => 365
```

## Contract

- `date - date` は `timedelta` を返し、`.days` が暦日差。左辺が後の日付なら正、前なら負、同じ日なら `0`
- 時刻を捨てるので、`datetime` は `.date()` にしてから引く。2 分しか離れていなくても日付が変われば `1`
- 入力を変更しない。`date` / `datetime` は不変
- `datetime - datetime` の `.days` は暦日差ではなく、経過時間を 24 時間で割って **−∞ 方向に丸めた** 値（`-2 分` → `-1`、`-12 時間` → `-1`、`+12 時間` → `0`）
- aware と naive の `datetime` を直接引くと `TypeError`。`.date()` にすると tzinfo が落ちて引ける
- `date - datetime`、`datetime - date` は `TypeError`
- `date` に `timedelta` を足せば逆演算になる（`earlier.date() + timedelta(days=1) == later.date()`）
- タイムゾーンに依存しない。aware な datetime はそれぞれ自分のゾーンの暦日で比較される

## Alternatives

- 「丸 1 日（24 時間）が何回あるか」なら `(later - earlier) // timedelta(days=1)`（こちらも −∞ 方向の丸め）、実時間の日数は `(later - earlier).total_seconds() / 86400`。ただし同じ `ZoneInfo` を持つ aware 同士の減算は壁時計の差（DST をまたぐと実時間と 1 時間ずれる）なので、実時間が欲しければ `later.astimezone(timezone.utc) - earlier.astimezone(timezone.utc)` のように UTC へ変換してから引く
- 同じ日かだけ知りたいなら `a.date() == b.date()`
- 週・月・年の暦単位差は `dateutil.relativedelta(later, earlier)`

## Pitfalls

- TypeScript（date-fns）の `differenceInCalendarDays` と同じ意味論。ただし `differenceInDays` はゼロ方向の切り捨てだが、Python の `(a - b).days` は −∞ 方向の丸めなので、負の差で 1 日ずれる
- 別ゾーンの aware な datetime を `.date()` で引くと、それぞれのローカル日付で比べる。JST の `03-01 00:30` と UTC の `02-29 20:00` は瞬間としては前者が早いのに差は `+1`。同じ基準で数えたいなら `astimezone()` で揃えてから `.date()` にする
- `(a - b).days` を暦日差のつもりで使うと、深夜をまたぐ短い間隔で `0` や `-1` になる
- 営業日数の計算には `numpy.busday_count` のような別の道具が要る

## Test

`examples/date-diff-days_test.py`
