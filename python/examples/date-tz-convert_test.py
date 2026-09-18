"""date-tz-convert: datetime.astimezone と zoneinfo の Contract を検証する。"""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pytest

JST = ZoneInfo("Asia/Tokyo")
NY = ZoneInfo("America/New_York")
UTC_0630 = datetime(2024, 3, 10, 6, 30, tzinfo=timezone.utc)


def test_astimezone_keeps_instant_and_changes_wall_clock() -> None:
    """同じ瞬間を別ゾーンの壁時計で表した新しい datetime を返す。入力は変わらない。"""
    tokyo = UTC_0630.astimezone(JST)
    assert tokyo.isoformat() == "2024-03-10T15:30:00+09:00"
    assert tokyo == UTC_0630
    assert tokyo.timestamp() == UTC_0630.timestamp()
    assert (tokyo.hour, tokyo.date().isoformat()) == (15, "2024-03-10")
    assert tokyo.tzinfo is JST
    assert UTC_0630.hour == 6 and UTC_0630.tzinfo is timezone.utc
    assert tokyo.astimezone(timezone.utc) == UTC_0630


def test_replace_tzinfo_relabels_instead_of_converting() -> None:
    """replace(tzinfo=) は壁時計をそのままにラベルだけ付け替えるので、瞬間が変わる。"""
    labeled = UTC_0630.replace(tzinfo=JST)
    assert labeled.isoformat() == "2024-03-10T06:30:00+09:00"
    assert labeled != UTC_0630
    assert UTC_0630.timestamp() - labeled.timestamp() == 9 * 3600


def test_naive_is_interpreted_as_local_time() -> None:
    """naive に astimezone すると実行環境のローカル時刻とみなす。引数無しはローカルへの変換。"""
    naive = datetime(2024, 3, 10, 6, 30)
    local = naive.astimezone()
    assert local.tzinfo is not None
    assert naive.astimezone(JST) == local
    assert naive.astimezone(JST) == naive.replace(tzinfo=local.tzinfo).astimezone(JST)


def test_naive_vs_aware_comparison() -> None:
    """naive と aware の == は False、< と引き算は TypeError。"""
    naive = datetime(2024, 3, 10, 6, 30)
    assert (naive == UTC_0630) is False
    with pytest.raises(TypeError, match="can't compare offset-naive and offset-aware"):
        naive < UTC_0630  # noqa: B015
    with pytest.raises(TypeError):
        naive - UTC_0630  # type: ignore[operator]


def test_nonexistent_wall_clock_in_dst_gap() -> None:
    """存在しない壁時計（NY 2024-03-10 02:30）は例外にならず fold=0 で切替前のオフセット。UTC 往復で正規化される。"""
    gap = datetime(2024, 3, 10, 2, 30, tzinfo=NY)
    assert gap.isoformat() == "2024-03-10T02:30:00-05:00"
    assert gap.astimezone(timezone.utc).isoformat() == "2024-03-10T07:30:00+00:00"
    assert gap.astimezone(timezone.utc).astimezone(NY).isoformat() == "2024-03-10T03:30:00-04:00"
    assert gap.replace(fold=1).isoformat() == "2024-03-10T02:30:00-04:00"


def test_ambiguous_wall_clock_uses_fold() -> None:
    """2 回ある壁時計（NY 2024-11-03 01:30）は fold=0 が 1 回目、fold=1 が 2 回目。UTC からの変換は正しい fold を付ける。"""
    first = datetime(2024, 11, 3, 1, 30, tzinfo=NY)
    second = first.replace(fold=1)
    assert first.isoformat() == "2024-11-03T01:30:00-04:00"
    assert second.isoformat() == "2024-11-03T01:30:00-05:00"
    assert second.astimezone(timezone.utc) - first.astimezone(timezone.utc) == timedelta(hours=1)
    from_utc = datetime(2024, 11, 3, 6, 30, tzinfo=timezone.utc).astimezone(NY)
    assert (from_utc.fold, from_utc.isoformat()) == (1, "2024-11-03T01:30:00-05:00")


def test_zoneinfo_lookup_cache_and_names() -> None:
    """無い名前は ZoneInfoNotFoundError（KeyError）。同じキーは同一インスタンス。strftime の %Z / %z。"""
    with pytest.raises(ZoneInfoNotFoundError) as info:
        ZoneInfo("Mars/Olympus")
    assert isinstance(info.value, KeyError)
    assert ZoneInfo("Asia/Tokyo") is JST
    assert JST.key == "Asia/Tokyo"
    assert UTC_0630.astimezone(JST).strftime("%Z %z") == "JST +0900"


def test_fromisoformat_z_and_fixed_offset_alternatives() -> None:
    """Alternatives: fromisoformat は Z を受け付け、固定オフセットは timezone(timedelta)。"""
    assert datetime.fromisoformat("2024-03-10T06:30:00Z").astimezone(JST).isoformat() == "2024-03-10T15:30:00+09:00"
    assert UTC_0630.astimezone(timezone(timedelta(hours=9))).isoformat() == "2024-03-10T15:30:00+09:00"


def test_timedelta_across_dst_is_not_normalized() -> None:
    """Pitfalls: 同じゾーンでの加算は瞬間を進めるが、結果が DST の隙間に入っても正規化されない。UTC 経由で正規化する。"""
    before = datetime(2024, 3, 10, 1, 30, tzinfo=NY)
    after = before + timedelta(hours=1)
    assert after.isoformat() == "2024-03-10T02:30:00-05:00"
    assert after.astimezone(timezone.utc) - before.astimezone(timezone.utc) == timedelta(hours=1)
    assert after.astimezone(timezone.utc).astimezone(NY).isoformat() == "2024-03-10T03:30:00-04:00"


def test_ambiguous_time_cross_zone_equality_is_false() -> None:
    """Pitfalls: fold が意味を持つ時刻は別ゾーンとの == が常に False。同じゾーン同士は fold を無視する。"""
    first = datetime(2024, 11, 3, 1, 30, tzinfo=NY)
    second = first.replace(fold=1)
    assert first == second
    assert (first == first.astimezone(timezone.utc)) is False
    assert (second == second.astimezone(timezone.utc)) is False
    assert first.astimezone(timezone.utc) == datetime(2024, 11, 3, 5, 30, tzinfo=timezone.utc)
