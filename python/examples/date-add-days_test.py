"""date-add-days: datetime / date + timedelta(days=n) の Contract を検証する。"""

from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

JST = ZoneInfo("Asia/Tokyo")
NY = ZoneInfo("America/New_York")


def test_add_and_subtract_days() -> None:
    """正の日数で加算、負の日数または減算で戻せる。"""
    d = datetime(2024, 2, 29, 13, 45)
    assert d + timedelta(days=1) == datetime(2024, 3, 1, 13, 45)
    assert d + timedelta(days=-1) == datetime(2024, 2, 28, 13, 45)
    assert d - timedelta(days=1) == datetime(2024, 2, 28, 13, 45)


def test_returns_new_object_without_mutating_input() -> None:
    """入力を変更せず新しいオブジェクトを返す。days=0 でも別インスタンス。"""
    d = datetime(2024, 2, 29, 13, 45)
    result = d + timedelta(days=0)
    assert result == d
    assert result is not d
    d + timedelta(days=10)
    assert d == datetime(2024, 2, 29, 13, 45)


def test_calendar_rollover_and_leap_year() -> None:
    """月末・年末・うるう年の繰り越しはカレンダーどおり。"""
    assert date(2024, 2, 29) + timedelta(days=1) == date(2024, 3, 1)
    assert date(2024, 12, 31) + timedelta(days=1) == date(2025, 1, 1)
    assert date(2023, 2, 28) + timedelta(days=1) == date(2023, 3, 1)
    assert date(2024, 2, 29) + timedelta(days=365) == date(2025, 2, 28)
    assert date(2024, 2, 29) + timedelta(days=366) == date(2025, 3, 1)


def test_time_and_tzinfo_are_preserved() -> None:
    """時・分・秒・マイクロ秒と tzinfo は保たれる。"""
    d = datetime(2024, 2, 29, 13, 45, 7, 123456, tzinfo=JST)
    r = d + timedelta(days=1)
    assert r == datetime(2024, 3, 1, 13, 45, 7, 123456, tzinfo=JST)
    assert r.tzinfo is JST


def test_fractional_days_are_36_hours() -> None:
    """days=1.5 は 36 時間。datetime では時刻が 12 時間進む。"""
    assert timedelta(days=1.5) == timedelta(days=1, hours=12)
    assert timedelta(days=1.5).total_seconds() == 36 * 3600
    assert datetime(2024, 2, 29, 13, 45) + timedelta(days=1.5) == datetime(2024, 3, 2, 1, 45)


def test_date_ignores_sub_day_part() -> None:
    """date に足すと日未満の部分は無視される。"""
    assert date(2024, 2, 29) + timedelta(days=1.5) == date(2024, 3, 1)
    assert date(2024, 2, 29) + timedelta(hours=36) == date(2024, 3, 1)
    assert date(2024, 2, 29) + timedelta(hours=23) == date(2024, 2, 29)


def test_aware_add_keeps_wall_clock_across_dst() -> None:
    """aware でも壁時計をそのまま進める。DST 切替をまたぐと実時間は 23 または 25 時間。"""
    spring = datetime(2024, 3, 9, 12, 0, tzinfo=NY)
    after_spring = spring + timedelta(days=1)
    assert after_spring == datetime(2024, 3, 10, 12, 0, tzinfo=NY)
    assert after_spring.utcoffset() == timedelta(hours=-4)
    assert after_spring.timestamp() - spring.timestamp() == 23 * 3600
    assert after_spring.astimezone(timezone.utc) - spring.astimezone(timezone.utc) == timedelta(hours=23)

    fall = datetime(2024, 11, 2, 12, 0, tzinfo=NY)
    after_fall = fall + timedelta(days=1)
    assert after_fall == datetime(2024, 11, 3, 12, 0, tzinfo=NY)
    assert after_fall.timestamp() - fall.timestamp() == 25 * 3600


def test_landing_on_nonexistent_time_does_not_raise() -> None:
    """存在しない時刻（DST 開始時のギャップ）に着地しても例外は出ない。"""
    d = datetime(2024, 3, 9, 2, 30, tzinfo=NY) + timedelta(days=1)
    assert d == datetime(2024, 3, 10, 2, 30, tzinfo=NY)
    assert d.utcoffset() == timedelta(hours=-5)


def test_utc_add_for_exact_24_hours() -> None:
    """Pitfalls の方法: UTC で足してから戻せば実時間ちょうど 24 時間になる。"""
    spring = datetime(2024, 3, 9, 12, 0, tzinfo=NY)
    exact = (spring.astimezone(timezone.utc) + timedelta(days=1)).astimezone(NY)
    assert exact.timestamp() - spring.timestamp() == 24 * 3600
    assert exact == datetime(2024, 3, 10, 13, 0, tzinfo=NY)


def test_out_of_range_raises_overflow_error() -> None:
    """datetime.max を超えると OverflowError。大きすぎる timedelta も OverflowError。"""
    with pytest.raises(OverflowError):
        datetime(9999, 12, 31) + timedelta(days=1)
    with pytest.raises(OverflowError):
        timedelta(days=1e9)


def test_invalid_operands_raise_type_error() -> None:
    """datetime + int や days='1' は TypeError。"""
    with pytest.raises(TypeError):
        datetime(2024, 2, 29) + 1  # type: ignore[operator]
    with pytest.raises(TypeError):
        timedelta(days="1")  # type: ignore[arg-type]


def test_weeks_argument() -> None:
    """weeks=1 は 7 日。"""
    assert date(2024, 2, 29) + timedelta(weeks=1) == date(2024, 3, 7)
