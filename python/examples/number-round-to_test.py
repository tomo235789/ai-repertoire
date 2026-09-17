# カード number-round-to の Contract を検証するテスト
import math
from decimal import ROUND_HALF_UP, Decimal

import pytest


def test_return_type_depends_on_ndigits():
    """ndigits 省略なら int、指定すると入力と同じ型"""
    assert round(1.2345) == 1
    assert type(round(1.2345)) is int
    assert round(1.2345, 2) == 1.23
    assert type(round(2.5, 0)) is float
    assert round(2.5, 0) == 2.0
    assert type(round(5, 2)) is int


def test_half_to_even():
    """.5 は偶数丸め"""
    assert round(0.5) == 0
    assert round(1.5) == 2
    assert round(2.5) == 2
    assert round(-2.5) == -2
    assert round(-1.5) == -2


def test_negative_ndigits_rounds_integers_half_to_even():
    """負の ndigits は 10 の位・100 の位で丸め、int でも偶数丸め"""
    assert round(1250, -2) == 1200
    assert round(1350, -2) == 1400
    assert round(1234.5678, -2) == 1200.0


def test_float_representation_error_is_not_corrected():
    """浮動小数点の表現誤差は補正しない"""
    assert round(2.675, 2) == 2.67
    assert round(1.005, 2) == 1.0


def test_decimal_uses_decimal_rounding_mode():
    """Decimal は既定 ROUND_HALF_EVEN で丸める"""
    assert round(Decimal("2.675"), 2) == Decimal("2.68")
    assert round(Decimal("2.5")) == 2


def test_invalid_arguments_raise():
    """ndigits が int でないと TypeError。省略時に NaN は ValueError、inf は OverflowError"""
    with pytest.raises(TypeError):
        round(1.5, 1.0)
    with pytest.raises(ValueError):
        round(math.nan)
    with pytest.raises(OverflowError):
        round(math.inf)
    assert math.isnan(round(math.nan, 2))
    assert round(math.inf, 2) == math.inf


def test_negative_zero():
    """round(-0.4, 0) は -0.0"""
    result = round(-0.4, 0)
    assert result == 0.0
    assert math.copysign(1, result) == -1


def test_half_up_alternative_with_decimal():
    """Alternatives: Decimal(str(x)).quantize(ROUND_HALF_UP) で一般的な四捨五入。Decimal(float) は誤差が入る"""
    assert Decimal(str(2.675)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == Decimal("2.68")
    assert Decimal("0.5").quantize(Decimal("1"), rounding=ROUND_HALF_UP) == Decimal("1")
    assert Decimal(2.675).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP) == Decimal("2.67")


def test_format_string_is_also_half_to_even():
    """Alternatives: f-string の書式指定も偶数丸め"""
    assert f"{2.5:.0f}" == "2"
    assert f"{0.125:.2f}" == "0.12"
    assert f"{1.5:.2f}" == "1.50"
