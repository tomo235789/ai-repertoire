# カード number-clamp の Contract を検証するテスト
import math

import pytest


def clamp(x, lo, hi):
    return min(max(x, lo), hi)


def test_clamps_into_range_inclusive():
    """範囲外は境界値に置き換え、境界値は含む"""
    assert clamp(120, 0, 100) == 100
    assert clamp(-5, 0, 100) == 0
    assert clamp(42, 0, 100) == 42
    assert clamp(0, 0, 100) == 0
    assert clamp(100, 0, 100) == 100


def test_lo_greater_than_hi_always_returns_hi():
    """lo > hi なら常に hi が返る"""
    assert clamp(50, 100, 0) == 0
    assert clamp(-10, 100, 0) == 0
    assert clamp(200, 100, 0) == 0


def test_returns_one_of_the_arguments_without_conversion():
    """返り値は引数のいずれかそのもので、型変換しない"""
    x = 5
    assert clamp(x, 0, 10) is x
    assert type(clamp(5, 0.0, 10)) is int
    assert type(clamp(-5, 0.0, 10)) is float


def test_nan_handling():
    """x が NaN なら NaN。lo / hi の片方が NaN ならその境界だけが効かず、もう片方は効く"""
    assert math.isnan(clamp(math.nan, 0, 100))
    assert clamp(50, math.nan, 100) == 50
    assert clamp(-5, math.nan, 100) == -5
    assert clamp(200, math.nan, 100) == 100  # hi は効く
    assert clamp(200, 0, math.nan) == 200
    assert clamp(-5, 0, math.nan) == 0  # lo は効く


def test_does_not_mutate_arguments():
    """引数を変更しない（イミュータブルな数値なので値が変わらないことを確認）"""
    x, lo, hi = 120, 0, 100
    clamp(x, lo, hi)
    assert (x, lo, hi) == (120, 0, 100)


def test_incomparable_types_raise_type_error():
    """比較できない型を渡すと TypeError"""
    with pytest.raises(TypeError):
        clamp("a", 0, 1)


def test_alternatives():
    """Alternatives: max(lo, min(x, hi)) は lo > hi で lo を返す。sorted は lo <= hi なら同じ"""
    assert max(0, min(120, 100)) == 100
    assert max(100, min(50, 0)) == 100
    assert sorted((120, 0, 100))[1] == 100
    assert sorted((50, 100, 0))[1] == 50


def test_no_builtin_clamp():
    """Pitfalls: math モジュールに clamp は無い"""
    assert not hasattr(math, "clamp")
