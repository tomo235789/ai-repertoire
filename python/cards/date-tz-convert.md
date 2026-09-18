---
id: date-tz-convert
lang: python
title: 日時を別のタイムゾーンで扱う
tags: [タイムゾーン変換, 時差, 別地域の時刻, 夏時間, timezone, tz, zoneinfo, DST]
lib: stdlib
fn: datetime.astimezone
since: "3.9"
verified: 2026-09-17
status: public
---

`dt.astimezone(ZoneInfo("Asia/Tokyo"))` で同じ瞬間を指定タイムゾーンの壁時計で表した新しい `datetime` を得る。表示や日付の境界の計算を、実行環境のタイムゾーンに依存せず行うために使う。

## Signature

```python
datetime.astimezone(tz=None)
```

## Usage

```python
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

utc = datetime(2024, 3, 10, 6, 30, tzinfo=timezone.utc)
tokyo = utc.astimezone(ZoneInfo("Asia/Tokyo"))
tokyo.isoformat()         # => '2024-03-10T15:30:00+09:00'（同じ瞬間。tokyo == utc は True）
tokyo.hour, tokyo.date()  # => (15, datetime.date(2024, 3, 10))
utc.replace(tzinfo=ZoneInfo("Asia/Tokyo")).isoformat()  # => '2024-03-10T06:30:00+09:00'（変換ではなくラベル付け。別の瞬間）
datetime(2024, 3, 10, 6, 30).astimezone(ZoneInfo("Asia/Tokyo"))  # naive は実行環境のローカル時刻とみなして変換される
```

## Contract

- aware な `datetime` に `astimezone(tz)` すると **同じ瞬間** を `tz` の壁時計で表した新しい `datetime` を返す（`==` と `timestamp()` は元と等しく、`hour` / `date()` は変わる）。入力は変更しない
- `replace(tzinfo=tz)` は壁時計の数字をそのままに `tzinfo` だけ付け替える。瞬間が変わる（`timestamp()` がオフセット分ずれる）ので変換には使わない。naive に `tzinfo` を付ける用途に限る
- naive な `datetime` に `astimezone(tz)` すると **実行環境のローカルタイムゾーン** の時刻とみなして変換する。`astimezone()` と引数無しで呼ぶとローカルタイムゾーンへの変換
- naive と aware の `==` は例外にならず常に `False`。`<` や引き算は `TypeError`（`can't compare offset-naive and offset-aware datetimes`）
- DST の切り替えで **存在しない壁時計**（`America/New_York` の 2024-03-10 02:30）を作っても例外は出ず、`fold=0` なら切替前のオフセット（`-05:00`）が付く。UTC に直して戻すと `03:30-04:00` に正規化される。**2 回ある壁時計**（2024-11-03 01:30）は `fold=0` が 1 回目（`-04:00`）、`fold=1` が 2 回目（`-05:00`）で、UTC から変換したときは正しい `fold` が付く
- `ZoneInfo(key)` は IANA 名（`Asia/Tokyo` / `UTC`）を受け取り、無い名前は `ZoneInfoNotFoundError`（`KeyError` のサブクラス）。同じキーは同一インスタンスを返す（`ZoneInfo("Asia/Tokyo") is ZoneInfo("Asia/Tokyo")`）。`strftime("%Z %z")` は `JST +0900`

## Alternatives

- 固定オフセットだけなら `timezone(timedelta(hours=9))`（DST の無いゾーン向け。`ZoneInfo` の方が名前で意図が分かる）
- ISO 8601 文字列からなら `datetime.fromisoformat("2024-03-10T06:30:00Z").astimezone(ZoneInfo("Asia/Tokyo"))`（`Z` は 3.11 から受け付ける）
- 特定ゾーンでの日の始まりはカード date-start-of-day（先に `astimezone` してから丸める）
- 現在時刻は `datetime.now(ZoneInfo("Asia/Tokyo"))`。`datetime.now()` の naive は使わない（`ruff.toml` の `utcnow` 禁止も同じ理由）

## Pitfalls

- TypeScript（`TZDate`）は瞬間と壁時計を 1 つのオブジェクトが両方持つが、Python は `astimezone` した **別の `datetime`** を作る。元の変数は元のゾーンのまま
- `replace(tzinfo=...)` を変換のつもりで使うと 9 時間ずれる。「変換は `astimezone`、ラベル付けは `replace`」
- naive な値を `astimezone` に通すとサーバーの `TZ` 設定で結果が変わる。CI（UTC）と本番（JST）で違う値になる典型。入口で aware にする
- 同じゾーンの aware な `datetime` への `timedelta` 加算は **壁時計** の演算で、DST をまたいでも経過時間は 23 時間や 25 時間になり、結果が存在しない時刻（DST の隙間）になっても正規化されない。DST をまたぐ計算は UTC で行うか、`astimezone(timezone.utc).astimezone(tz)` で正規化する
- `fold` が意味を持つ時刻（2 回ある壁時計）は別ゾーンの値との `==` が常に `False`（同じゾーン同士では `fold` を無視して `True`）。比較は UTC に揃えてから行う
- Windows や最小構成のコンテナには IANA データベースが無く `ZoneInfoNotFoundError` になる。`tzdata` パッケージを入れる

## Test

`examples/date-tz-convert_test.py`
