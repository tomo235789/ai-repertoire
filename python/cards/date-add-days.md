---
id: date-add-days
lang: python
title: 日付に日数を加算する
tags: [日付加算, 日数, 減算, 月末, うるう年, add-days, plus, date-math]
lib: stdlib
fn: datetime.timedelta
since: "3.0"
verified: 2026-09-17
status: public
---

datetime / date に `timedelta(days=n)` を足して新しい値を得る（負数で減算）。期限日や有効期間の計算に使う。

## Signature

```python
datetime.timedelta(days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0)
```

## Usage

```python
from datetime import date, datetime, timedelta

d = datetime(2024, 2, 29, 13, 45)
d + timedelta(days=1)    # => datetime(2024, 3, 1, 13, 45)
d - timedelta(days=1)    # => datetime(2024, 2, 28, 13, 45)
d + timedelta(days=366)  # => datetime(2025, 3, 1, 13, 45)
date(2024, 12, 31) + timedelta(days=1)  # => date(2025, 1, 1)
d                        # 変わらない
```

## Contract

- 入力を変更せず新しいオブジェクトを返す（`days=0` でも別インスタンス）。datetime も date も不変
- 月末・年末・うるう年の繰り越しはカレンダーどおり（`2024-02-29` + 1 → `2024-03-01`、+ 365 → `2025-02-28`）
- 時・分・秒・マイクロ秒と `tzinfo` はそのまま保たれる
- `days` は float も受け、`timedelta(days=1.5)` は **36 時間**。`datetime` に足すと時刻が 12 時間進む。`date` に足すと正規化後の `.days` だけが使われる（`date(2024, 2, 29) + timedelta(days=1.5)` → `date(2024, 3, 1)`、`+ timedelta(hours=23)` → `date(2024, 2, 29)`）。負の小数は −∞ 方向に正規化されるので `timedelta(days=-1.5)` は `days=-2, seconds=43200` となり、`date(2024, 3, 1) + timedelta(days=-1.5)` → `date(2024, 2, 28)`（ゼロ方向の切り捨てではない）
- aware な datetime に足しても壁時計の時刻をそのまま進める。DST 切替をまたぐと実時間の差は 23 または 25 時間になり、`timestamp()` の差はそれを反映する。存在しない時刻に着地しても例外は出ない
- 範囲外（`datetime.max` を超える）は `OverflowError`。`timedelta(days=1e9)` のような大きすぎる値も `OverflowError`
- `datetime + int` や `timedelta(days="1")` は `TypeError`

## Alternatives

- 週は `timedelta(weeks=1)`。月・年は `timedelta` に無いので `dateutil.relativedelta(months=1)`（月末クランプあり）か `calendar` で自前計算
- 減算は負数を渡すか `d - timedelta(days=1)`
- 経過日数を求めるのは `date-diff-days`

## Pitfalls

- TypeScript（date-fns）の `addDays(d, 1.5)` は小数を切り捨てて 1 日だが、`timedelta(days=1.5)` は 36 時間。日数は整数で渡すか、意図して時間単位で足す
- `timedelta` は月・年を表せない。`timedelta(days=30)` は「1 か月」ではない
- aware な値の DST は zoneinfo でも自動補正されない。「ちょうど 24 時間後」が欲しければ `astimezone(timezone.utc)` で UTC にしてから足し、元のゾーンに戻す
- naive と aware の混在は加算では問題にならないが、その後の比較・減算で `TypeError` になる

## Test

`examples/date-add-days_test.py`
