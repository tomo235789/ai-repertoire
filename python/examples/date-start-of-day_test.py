"""date-start-of-day: datetime.combine(date, time.min, tzinfo=...) の Contract を検証する。"""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

JST = ZoneInfo("Asia/Tokyo")
NY = ZoneInfo("America/New_York")


def start_of_day(dt: datetime) -> datetime:
    """カードの Usage と同じ式。"""
    return datetime.combine(dt.date(), time.min, tzinfo=dt.tzinfo)


def test_truncates_time_and_keeps_date() -> None:
    """時刻を 00:00:00.000000 にし、日付は変えない。"""
    dt = datetime(2024, 2, 29, 13, 45, 7, 123456, tzinfo=JST)
    assert start_of_day(dt) == datetime(2024, 2, 29, 0, 0, tzinfo=JST)
    assert start_of_day(dt).isoformat() == "2024-02-29T00:00:00+09:00"


def test_returns_new_object_without_mutating_input() -> None:
    """入力を変更せず新しい datetime を返す。"""
    dt = datetime(2024, 2, 29, 13, 45, 7, 123456, tzinfo=JST)
    result = start_of_day(dt)
    assert result is not dt
    assert dt.hour == 13
    assert dt == datetime(2024, 2, 29, 13, 45, 7, 123456, tzinfo=JST)


def test_keeps_tzinfo_for_aware_and_naive_for_naive() -> None:
    """aware は同じ tzinfo の aware、naive は naive のまま。"""
    aware = start_of_day(datetime(2024, 2, 29, 13, 45, tzinfo=JST))
    assert aware.tzinfo is JST
    assert aware.utcoffset() == timedelta(hours=9)
    naive = start_of_day(datetime(2024, 2, 29, 13, 45))
    assert naive.tzinfo is None
    assert naive == datetime(2024, 2, 29)


def test_omitting_tzinfo_drops_timezone() -> None:
    """tzinfo を省略すると time.min の tzinfo（None）が使われ、結果は naive になる。"""
    dt = datetime(2024, 2, 29, 13, 45, tzinfo=JST)
    assert time.min.tzinfo is None
    assert datetime.combine(dt.date(), time.min).tzinfo is None


def test_tzinfo_argument_overrides_time_tzinfo() -> None:
    """tzinfo 引数は time 側の tzinfo より優先される。"""
    d = date(2024, 2, 29)
    assert datetime.combine(d, time(tzinfo=NY)).tzinfo is NY
    assert datetime.combine(d, time(tzinfo=NY), tzinfo=JST).tzinfo is JST


def test_is_idempotent() -> None:
    """冪等。結果をもう一度渡しても同じ。"""
    dt = datetime(2024, 2, 29, 13, 45, 7, 123456, tzinfo=JST)
    once = start_of_day(dt)
    assert start_of_day(once) == once


def test_fold_is_reset_but_replace_keeps_it() -> None:
    """combine は fold を 0 にリセットし、replace は fold を保つ。"""
    dt = datetime(2024, 11, 3, 1, 30, fold=1, tzinfo=NY)
    assert dt.fold == 1
    combined = start_of_day(dt)
    assert combined.fold == 0
    assert combined.isoformat() == "2024-11-03T00:00:00-04:00"
    replaced = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    assert replaced.fold == 1
    assert replaced == combined


def test_replace_alternative_gives_same_value() -> None:
    """Alternatives の replace は同じ値になり tzinfo を保つ。"""
    dt = datetime(2024, 2, 29, 13, 45, 7, 123456, tzinfo=JST)
    replaced = dt.replace(hour=0, minute=0, second=0, microsecond=0)
    assert replaced == start_of_day(dt)
    assert replaced.tzinfo is JST


def test_datetime_as_first_argument_uses_its_date_and_str_raises() -> None:
    """第 1 引数に datetime を渡すと日付部分だけが使われる。str は TypeError。"""
    dt = datetime(2024, 2, 29, 13, 45, tzinfo=JST)
    assert datetime.combine(dt, time.min, tzinfo=dt.tzinfo) == start_of_day(dt)
    with pytest.raises(TypeError):
        datetime.combine("2024-02-29", time.min)  # type: ignore[arg-type]


def test_subclass_is_preserved() -> None:
    """datetime のサブクラスで呼ぶとそのサブクラスで返る。"""

    class MyDateTime(datetime):
        pass

    result = MyDateTime.combine(date(2024, 2, 29), time.min)
    assert type(result) is MyDateTime


def test_independent_of_local_timezone_and_utc_conversion() -> None:
    """結果は tzinfo に従い実行環境に依存しない。UTC の 0 時が欲しければ先に astimezone する。"""
    dt = datetime(2024, 2, 29, 3, 0, tzinfo=JST)
    assert start_of_day(dt).astimezone(timezone.utc) == datetime(2024, 2, 28, 15, 0, tzinfo=timezone.utc)
    assert start_of_day(dt.astimezone(timezone.utc)) == datetime(2024, 2, 28, 0, 0, tzinfo=timezone.utc)


def test_nonexistent_midnight_gets_pre_transition_offset() -> None:
    """0 時が存在しない日でも例外は出ず、切替前のオフセットが付く。UTC では実際の日の始まりと一致する。"""
    sp = ZoneInfo("America/Sao_Paulo")
    result = datetime.combine(date(2018, 11, 4), time.min, tzinfo=sp)
    assert result.isoformat() == "2018-11-04T00:00:00-03:00"
    assert result.astimezone(timezone.utc) == datetime(2018, 11, 4, 3, 0, tzinfo=timezone.utc)
    assert result.astimezone(timezone.utc) == datetime(2018, 11, 4, 1, 0, tzinfo=timezone(timedelta(hours=-2)))
