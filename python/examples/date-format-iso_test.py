"""date-format-iso: datetime.isoformat の Contract を検証する。"""

from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

JST = ZoneInfo("Asia/Tokyo")


def test_aware_has_offset_naive_has_none() -> None:
    """aware にはオフセットが付き、naive には付かない。"""
    naive = datetime(2024, 2, 29, 13, 45, 7)
    assert naive.isoformat() == "2024-02-29T13:45:07"
    assert naive.replace(tzinfo=JST).isoformat() == "2024-02-29T13:45:07+09:00"
    assert naive.replace(tzinfo=timezone(timedelta(hours=-3))).isoformat() == "2024-02-29T13:45:07-03:00"


def test_utc_is_plus_zero_not_z() -> None:
    """UTC は +00:00 になり Z にはならない。"""
    d = datetime(2024, 2, 29, 13, 45, 7, tzinfo=timezone.utc)
    assert d.isoformat() == "2024-02-29T13:45:07+00:00"
    assert d.isoformat().endswith("+00:00")


def test_timespec_auto_depends_on_microsecond() -> None:
    """timespec='auto' はマイクロ秒が 0 なら秒まで、0 以外なら 6 桁まで出す。"""
    assert datetime(2024, 2, 29, 13, 45, 7).isoformat() == "2024-02-29T13:45:07"
    assert datetime(2024, 2, 29, 13, 45, 7, 123456).isoformat() == "2024-02-29T13:45:07.123456"


def test_timespec_fixes_digits() -> None:
    """timespec で桁を固定できる。milliseconds はマイクロ秒 0 でも .000 を出す。"""
    d = datetime(2024, 2, 29, 13, 45, 7, 123456)
    assert d.isoformat(timespec="hours") == "2024-02-29T13"
    assert d.isoformat(timespec="minutes") == "2024-02-29T13:45"
    assert d.isoformat(timespec="seconds") == "2024-02-29T13:45:07"
    assert d.isoformat(timespec="milliseconds") == "2024-02-29T13:45:07.123"
    assert d.isoformat(timespec="microseconds") == "2024-02-29T13:45:07.123456"
    assert d.replace(microsecond=0).isoformat(timespec="milliseconds") == "2024-02-29T13:45:07.000"


def test_digits_are_truncated_not_rounded() -> None:
    """桁を落とすときは切り捨てで、四捨五入しない。"""
    d = datetime(2024, 2, 29, 13, 45, 7, 999999)
    assert d.isoformat(timespec="milliseconds") == "2024-02-29T13:45:07.999"
    assert d.isoformat(timespec="seconds") == "2024-02-29T13:45:07"


def test_year_is_zero_padded_to_four_digits() -> None:
    """年は 4 桁ゼロ埋め。"""
    assert datetime(1, 1, 1).isoformat() == "0001-01-01T00:00:00"


def test_sep_and_timespec_validation() -> None:
    """sep は 1 文字でなければ TypeError、未知の timespec は ValueError。"""
    d = datetime(2024, 2, 29, 13, 45, 7)
    assert d.isoformat(" ") == "2024-02-29 13:45:07"
    with pytest.raises(TypeError):
        d.isoformat(sep="::")
    with pytest.raises(ValueError):
        d.isoformat(timespec="nanoseconds")


def test_input_is_not_mutated_and_independent_of_local_timezone() -> None:
    """入力を変更せず、tzinfo が無ければオフセットを付けないだけで実行環境には依存しない。"""
    d = datetime(2024, 2, 29, 13, 45, 7, tzinfo=JST)
    before = d.isoformat()
    d.isoformat(timespec="minutes")
    assert d == datetime(2024, 2, 29, 13, 45, 7, tzinfo=JST)
    assert d.isoformat() == before


def test_date_and_time_isoformat() -> None:
    """date.isoformat は日付だけ、time.isoformat は時刻部だけを返す。ZoneInfo 付きの time にはオフセットが付かない。"""
    assert date(2024, 2, 29).isoformat() == "2024-02-29"
    assert time(13, 45, 7, 123456).isoformat() == "13:45:07.123456"
    assert time(13, 45, 7, tzinfo=timezone(timedelta(hours=9))).isoformat() == "13:45:07+09:00"
    assert time(13, 45, 7, tzinfo=JST).isoformat() == "13:45:07"


def test_fromisoformat_round_trip() -> None:
    """fromisoformat で逆変換でき、Z 付きも受け付ける。"""
    d = datetime(2024, 2, 29, 13, 45, 7, tzinfo=JST)
    parsed = datetime.fromisoformat(d.isoformat())
    assert parsed == d
    assert parsed.utcoffset() == timedelta(hours=9)
    z = datetime.fromisoformat("2024-02-29T13:45:07Z")
    assert z == datetime(2024, 2, 29, 13, 45, 7, tzinfo=timezone.utc)
    assert datetime.fromisoformat("20240229T134507") == datetime(2024, 2, 29, 13, 45, 7)


def test_utc_z_alternative() -> None:
    """Alternatives の Z 付き UTC 変換。JST の深夜は UTC では前日になる。"""
    d = datetime(2024, 2, 29, 0, 30, tzinfo=JST)
    assert d.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z") == "2024-02-28T15:30:00Z"
    assert d.strftime("%Y-%m-%dT%H:%M:%S%z") == "2024-02-29T00:30:00+0900"
