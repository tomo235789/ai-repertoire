"""date-diff-days: date 同士の減算による暦日差の Contract を検証する。"""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

JST = ZoneInfo("Asia/Tokyo")
NY = ZoneInfo("America/New_York")

LATER = datetime(2024, 3, 1, 0, 1)
EARLIER = datetime(2024, 2, 29, 23, 59)


def test_date_subtraction_returns_timedelta_with_calendar_days() -> None:
    """date - date は timedelta を返し、.days が暦日差。"""
    diff = date(2024, 3, 1) - date(2024, 2, 29)
    assert isinstance(diff, timedelta)
    assert diff == timedelta(days=1)
    assert diff.days == 1
    assert (date(2025, 3, 1) - date(2024, 3, 1)).days == 365


def test_sign_depends_on_operand_order() -> None:
    """左辺が後なら正、前なら負、同じ日なら 0。"""
    assert (LATER.date() - EARLIER.date()).days == 1
    assert (EARLIER.date() - LATER.date()).days == -1
    assert (date(2024, 2, 29) - date(2024, 2, 29)).days == 0


def test_time_of_day_is_ignored() -> None:
    """時刻を捨てるので、2 分差でも日付が変われば 1。同じ日なら時刻に関係なく 0。"""
    assert (LATER.date() - EARLIER.date()).days == 1
    assert (datetime(2024, 3, 1, 23, 59).date() - datetime(2024, 3, 1, 0, 0).date()).days == 0


def test_inputs_are_not_mutated() -> None:
    """入力は変わらない。"""
    a, b = date(2024, 3, 1), date(2024, 2, 29)
    a - b
    assert a == date(2024, 3, 1)
    assert b == date(2024, 2, 29)


def test_datetime_difference_days_floors_toward_negative_infinity() -> None:
    """datetime - datetime の .days は 24 時間単位で −∞ 方向に丸める。"""
    assert (LATER - EARLIER) == timedelta(minutes=2)
    assert (LATER - EARLIER).days == 0
    assert (EARLIER - LATER).days == -1
    assert (datetime(2024, 3, 1, 12) - datetime(2024, 3, 1, 0)).days == 0
    assert (datetime(2024, 3, 1, 0) - datetime(2024, 3, 1, 12)).days == -1


def test_floor_division_by_one_day_also_floors() -> None:
    """Alternatives の timedelta // timedelta(days=1) も −∞ 方向の丸め。"""
    assert (LATER - EARLIER) // timedelta(days=1) == 0
    assert (EARLIER - LATER) // timedelta(days=1) == -1
    assert (LATER - EARLIER).total_seconds() / 86400 == pytest.approx(2 / 1440)


def test_mixing_aware_and_naive_datetime_raises() -> None:
    """aware と naive の datetime を直接引くと TypeError。.date() にすれば引ける。"""
    aware = datetime(2024, 3, 1, tzinfo=JST)
    naive = datetime(2024, 3, 1)
    with pytest.raises(TypeError):
        aware - naive
    assert (aware.date() - naive.date()).days == 0


def test_date_and_datetime_cannot_be_subtracted() -> None:
    """date - datetime、datetime - date は TypeError。"""
    with pytest.raises(TypeError):
        date(2024, 3, 1) - datetime(2024, 2, 29)  # type: ignore[operator]
    with pytest.raises(TypeError):
        datetime(2024, 3, 1) - date(2024, 2, 29)  # type: ignore[operator]


def test_adding_timedelta_is_the_inverse() -> None:
    """date + timedelta で逆演算になる。"""
    assert EARLIER.date() + timedelta(days=1) == LATER.date()
    assert LATER.date() - timedelta(days=1) == EARLIER.date()


def test_aware_compare_by_instant_but_dates_are_local() -> None:
    """aware 同士の比較（<）は実時刻で行われる。.date() にすると各自のローカル日付になるので、揃えるなら astimezone してから。"""
    jst = datetime(2024, 3, 1, 0, 30, tzinfo=JST)
    utc = datetime(2024, 2, 29, 20, 0, tzinfo=timezone.utc)
    assert jst < utc
    assert (jst.date() - utc.date()).days == 1
    assert (jst.astimezone(timezone.utc).date() - utc.date()).days == 0


def test_dst_day_counts_as_one_calendar_day() -> None:
    """DST 切替日（23 時間）も暦日では 1 日。"""
    a = datetime(2024, 3, 11, 0, 0, tzinfo=NY)
    b = datetime(2024, 3, 9, 0, 0, tzinfo=NY)
    assert (a.date() - b.date()).days == 2
    assert a.astimezone(timezone.utc) - b.astimezone(timezone.utc) == timedelta(days=1, hours=23)
