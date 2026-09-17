# カード number-sum-by の Contract を検証するテスト
import math
from decimal import Decimal

import pytest


def test_sums_extracted_values():
    """各要素から取り出した数値を合計する"""
    items = [{"name": "a", "qty": 2}, {"name": "b", "qty": 3}]
    assert sum(item["qty"] for item in items) == 5


def test_does_not_mutate_input():
    """入力を変更しない"""
    items = [{"qty": 2}, {"qty": 3}]
    sum(item["qty"] for item in items)
    assert items == [{"qty": 2}, {"qty": 3}]


def test_key_evaluated_once_per_element_in_order():
    """取り出し関数は各要素につき 1 回、先頭から順に評価される"""
    calls = []

    def key(x):
        calls.append(x)
        return x

    assert sum(key(x) for x in [1, 2, 3]) == 6
    assert calls == [1, 2, 3]


def test_empty_returns_start():
    """空なら start を返す。既定は int の 0"""
    result = sum(x for x in [])
    assert result == 0
    assert type(result) is int
    assert sum((x for x in []), 0.0) == 0.0
    assert sum((x for x in [2, 3]), 10) == 15


def test_non_numeric_raises_type_error():
    """str や None が混ざると TypeError。start が str でも TypeError"""
    with pytest.raises(TypeError):
        sum(["a", "b"])
    with pytest.raises(TypeError):
        sum([None, 1])
    with pytest.raises(TypeError):
        sum(["a"], "")


def test_float_sum_is_compensated():
    """float の合計は 3.12 以降のほとんどのビルドで補正付き加算になる（厳密な丸めは保証されないので近似で検証）"""
    assert math.isclose(sum([0.1] * 10), 1.0, rel_tol=0, abs_tol=1e-12)
    assert math.isclose(sum([0.1, 0.2, 0.3]), 0.6, rel_tol=0, abs_tol=1e-12)
    assert math.fsum([0.1] * 10) == 1.0


def test_nan_and_inf():
    """NaN があれば NaN。inf と -inf を両方含むと NaN"""
    assert math.isnan(sum([1, math.nan]))
    assert math.isnan(sum([math.inf, -math.inf]))


def test_bool_and_mixed_types():
    """bool は int として合計。int と float が混在すると float"""
    assert sum([True, True]) == 2
    assert type(sum([True, True])) is int
    assert sum([1, 2.5]) == 3.5
    assert type(sum([1, 2.5])) is float


def test_decimal_sum():
    """Alternatives: Decimal はそのまま合計できるが float と混ぜると TypeError"""
    assert sum([Decimal("1.1"), Decimal("2.2")]) == Decimal("3.3")
    with pytest.raises(TypeError):
        sum([Decimal("1"), 0.5])


def test_missing_key_handling():
    """Pitfalls: キーが欠けた要素は KeyError。get で補う"""
    items = [{"qty": 2}, {}]
    with pytest.raises(KeyError):
        sum(item["qty"] for item in items)
    assert sum(item.get("qty", 0) for item in items) == 2
