---
id: date-start-of-day
lang: python
title: 日付の時刻を 0 時に切り捨てる
tags: [日付の切り捨て, 0時, 日の始まり, 時刻除去, start-of-day, midnight, truncate-time, floor]
lib: stdlib
fn: datetime.combine
since: "3.6"
verified: 2026-09-17
status: public
---

datetime の時刻部分を同じタイムゾーンの 00:00:00 にした新しい datetime を返す。日単位のキーやグルーピング、範囲検索の下限に使う。

## Signature

```python
datetime.combine(date, time, tzinfo=time.tzinfo)
```

## Usage

```python
from datetime import datetime, time
from zoneinfo import ZoneInfo

dt = datetime(2024, 2, 29, 13, 45, 7, 123456, tzinfo=ZoneInfo("Asia/Tokyo"))
datetime.combine(dt.date(), time.min, tzinfo=dt.tzinfo)
# => datetime(2024, 2, 29, 0, 0, tzinfo=ZoneInfo("Asia/Tokyo"))
dt.hour  # => 13（元は変わらない）
```

## Contract

- 日付部分はそのまま、時刻を `time.min`（`00:00:00.000000`）にする
- 入力を変更せず新しい datetime を返す。`tzinfo=dt.tzinfo` を渡せば aware は同じ tzinfo の aware、naive は naive のまま
- `tzinfo` を省略すると `time` 側の tzinfo が使われる。`time.min` は naive なので **結果も naive になり、元の tzinfo は落ちる**
- 冪等。結果をもう一度渡しても同じ値
- `fold` は `0` にリセットされる
- 第 1 引数に `datetime` を渡すと、その日付部分だけが使われる。`str` を渡すと `TypeError`
- 実行環境のタイムゾーンに依存しない。`datetime` のサブクラスで呼ぶとそのサブクラスで返る

## Alternatives

- `dt.replace(hour=0, minute=0, second=0, microsecond=0)`。tzinfo と `fold` を保つ。同じ結果になるが、`fold=1` の値では `fold` が残る
- 日付だけでよければ `dt.date()`
- 特定のタイムゾーンでの 0 時が欲しいなら、先に `dt.astimezone(ZoneInfo("Asia/Tokyo"))` で変換してから丸める
- 日の終わりは `time.max`（`23:59:59.999999`）を組み合わせるか、翌日の 0 時を上限に `<` で比較する

## Pitfalls

- TypeScript（date-fns）の `startOfDay` は実行環境のローカルタイムゾーンで丸めるが、Python は `tzinfo` に従う。naive なら「どこのゾーンでもない 0 時」。日付キーとして保存するなら aware にしておく
- `tzinfo=dt.tzinfo` を忘れると naive になる。`time.min` に tzinfo は無い
- UTC の 0 時が欲しいのに JST の値をそのまま丸めると 9 時間ずれる。先に `astimezone(timezone.utc)`
- DST 開始が 0 時のゾーン（`America/Sao_Paulo` の 2018-11-04 など）では 0 時が存在しないが、例外は出ず切替前のオフセット（`-03:00`）が付く。UTC に直すと実際の日の始まり（`01:00-02:00`）と一致する

## Test

`examples/date-start-of-day_test.py`
