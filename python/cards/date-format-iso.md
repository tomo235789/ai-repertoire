---
id: date-format-iso
lang: python
title: 日付を ISO 8601 形式の文字列にする
tags: [日付フォーマット, ISO 8601, 文字列化, タイムゾーン, format, iso, date-string, timestamp]
lib: stdlib
fn: datetime.isoformat
since: "3.6"
verified: 2026-09-17
status: public
---

datetime を ISO 8601 文字列（`2024-02-29T13:45:07+09:00`）にする。API の送信値やログの日時表記に使う。

## Signature

```python
datetime.isoformat(sep='T', timespec='auto')
```

## Usage

```python
from datetime import datetime
from zoneinfo import ZoneInfo

d = datetime(2024, 2, 29, 13, 45, 7, 123456, tzinfo=ZoneInfo("Asia/Tokyo"))
d.isoformat()                       # => '2024-02-29T13:45:07.123456+09:00'
d.isoformat(timespec="seconds")     # => '2024-02-29T13:45:07+09:00'
d.isoformat(timespec="milliseconds")  # => '2024-02-29T13:45:07.123+09:00'
d.date().isoformat()                # => '2024-02-29'
d.isoformat(" ")                    # => '2024-02-29 13:45:07.123456+09:00'
```

## Contract

- aware な datetime には `utcoffset()` を `+09:00` の形で付ける。UTC でも `+00:00` であり `Z` にはならない。naive な datetime にはオフセットが付かない
- `timespec="auto"`（既定）は `microsecond` が 0 なら秒まで、0 以外なら `.123456` まで出す。`"hours"` / `"minutes"` / `"seconds"` / `"milliseconds"` / `"microseconds"` で桁を固定でき、`"milliseconds"` は `microsecond` が 0 でも `.000` を出す
- 桁を落とすときは切り捨て（`999999` → `.999`）。四捨五入しない
- 年は 4 桁ゼロ埋め（`0001-01-01T00:00:00`）
- `sep` は 1 文字でなければ `TypeError`。未知の `timespec` は `ValueError`
- 入力を変更しない純粋関数。実行環境のタイムゾーンに依存しない（tzinfo が無ければ付けないだけ）
- `date.isoformat()` は `'2024-02-29'`、`time.isoformat()` も同じ規則で時刻部だけを返す。ただし `time` に `ZoneInfo` を付けても日付が無いのでオフセットは決まらず付かない（固定オフセットの `timezone` なら付く）

## Alternatives

- 逆変換は `datetime.fromisoformat(s)`。3.11 以降は末尾の `Z` も受け付け、`timezone.utc` の aware な値を返す
- 常に UTC の `Z` 付きにしたいなら `d.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")`
- 任意の書式は `d.strftime("%Y-%m-%dT%H:%M:%S%z")`（`%z` は `+0900` でコロン無し）
- 現在時刻は naive な `datetime.now()` ではなく `datetime.now(timezone.utc)` か `datetime.now(ZoneInfo("Asia/Tokyo"))` で aware にしてから整形する

## Pitfalls

- TypeScript（date-fns）の `formatISO` は常にローカルのオフセットを付け、オフセット 0 なら `Z` を出し、ミリ秒を出さない。`isoformat()` は naive ならオフセット無し、UTC は `+00:00`、マイクロ秒があれば 6 桁まで出す。API の仕様が `Z` を要求するなら置換する
- naive な値をそのまま整形すると受け手がどのタイムゾーンか判断できない。aware にしてから整形する
- JS の `Date.toISOString()` のように自動で UTC に変換されない。`astimezone(timezone.utc)` を明示する
- `fromisoformat` は 3.11 以降で `20240229T134507` のような basic 形式も受けるが、3.10 以前は `isoformat()` の出力形式しか受けない

## Test

`examples/date-format-iso_test.py`
