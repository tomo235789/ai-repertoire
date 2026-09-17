# カード number-mean の Contract を検証するテスト
import math
from decimal import Decimal
from fractions import Fraction
from statistics import StatisticsError, fmean, mean

import pytest


def test_returns_float_mean():
    """算術平均を常に float で返す"""
    assert fmean([1, 2, 3, 4, 5]) == 3.0
    assert fmean([1, 2]) == 1.5
    assert type(fmean([1, 3])) is float
    assert type(fmean([Decimal("1"), Decimal("2")])) is float
    assert type(fmean([Fraction(1, 3), Fraction(2, 3)])) is float


def test_empty_raises_statistics_error():
    """空を渡すと StatisticsError（ValueError のサブクラス）"""
    with pytest.raises(StatisticsError):
        fmean([])
    with pytest.raises(StatisticsError):
        fmean(iter([]))
    assert issubclass(StatisticsError, ValueError)


def test_does_not_mutate_input_and_accepts_iterables():
    """入力を変更せず、イテレータや集合も受け付ける"""
    xs = [3, 1, 2]
    fmean(xs)
    assert xs == [3, 1, 2]
    assert fmean(iter([1, 2, 3])) == 2.0
    assert fmean({1, 2, 3}) == 2.0
    assert fmean(x for x in [2, 4]) == 3.0


def test_uses_fsum_then_divides():
    """合計は math.fsum で求めてから個数で割る"""
    assert fmean([0.1, 0.2, 0.3]) == 0.19999999999999998
    assert fmean([0.1, 0.2, 0.3]) == math.fsum([0.1, 0.2, 0.3]) / 3


def test_nan_and_inf():
    """NaN があれば NaN。inf を含めば inf。inf と -inf を両方含むと ValueError"""
    assert math.isnan(fmean([1, math.nan]))
    assert fmean([math.inf, 1]) == math.inf
    with pytest.raises(ValueError):
        fmean([math.inf, -math.inf])


def test_non_numeric_raises_and_bool_counts_as_int():
    """数値でない要素は TypeError。bool は 1 / 0"""
    with pytest.raises(TypeError):
        fmean([1, None])
    with pytest.raises(TypeError):
        fmean(["1", "2"])
    assert fmean([True, False]) == 0.5


def test_weights():
    """weights で加重平均。長さが違うと StatisticsError"""
    assert fmean([1, 2, 3], weights=[3, 1, 1]) == 1.6
    with pytest.raises(StatisticsError):
        fmean([1, 2], weights=[1])


def test_mean_alternative_keeps_input_type():
    """Alternatives: statistics.mean は入力の型を保ち、分数で厳密に計算する"""
    assert mean([1, 3]) == 2
    assert type(mean([1, 3])) is int
    assert mean([1, 2]) == 1.5
    assert mean([Fraction(1, 3), Fraction(2, 3)]) == Fraction(1, 2)
    assert mean([0.1, 0.2, 0.3]) == 0.2


def test_plain_division_alternative_raises_on_empty():
    """Alternatives: sum(xs) / len(xs) は空で ZeroDivisionError"""
    xs: list[float] = []
    with pytest.raises(ZeroDivisionError):
        sum(xs) / len(xs)


def test_empty_to_nan_idiom():
    """Pitfalls: 空を NaN にしたければ条件式で分ける"""
    xs: list[float] = []
    assert math.isnan(fmean(xs) if xs else math.nan)
