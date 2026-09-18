"""json-deep-equal: コンテナの == による構造比較の Contract を検証する。"""

import dataclasses
import datetime
import json
import math
from collections import Counter, OrderedDict, namedtuple
from decimal import Decimal
from fractions import Fraction

import pytest


def test_containers_compare_recursively() -> None:
    """dict はキー順を見ず、list / tuple は順序を見て、set は集合として比較する。"""
    assert {"a": 1, "b": [1, {"c": 2}]} == {"b": [1, {"c": 2}], "a": 1}
    assert [1, 2] != [2, 1]
    assert (1, 2) != (2, 1)
    assert {1, 2} == {2, 1}
    assert {"a": {1, 2}} == {"a": {2, 1}}
    assert OrderedDict(a=1, b=2) != OrderedDict(b=2, a=1)
    assert OrderedDict(a=1, b=2) == {"b": 2, "a": 1}


def test_different_container_types_are_not_equal() -> None:
    """コンテナの型が違えば False。set / frozenset と dict / OrderedDict は例外。"""
    assert [1] != (1,)
    assert {1} != [1]
    assert [] != {}
    assert {} != set()
    assert {"a": [1]} != {"a": (1,)}
    assert frozenset({1}) == {1}
    assert dict(a=1) == OrderedDict(a=1)


def test_numbers_compare_across_types() -> None:
    """数値は型をまたいで値で比較する。"""
    assert 1 == 1.0
    assert 1 == True  # noqa: E712
    assert 0 == False  # noqa: E712
    assert {"a": 1} == {"a": True}
    assert {1: "x"} == {True: "x"}
    assert [1.0] == [True]
    assert Decimal("1.0") == 1
    assert Fraction(1, 2) == 0.5
    assert Decimal("0.1") != 0.1
    assert 0.1 + 0.2 != 0.3
    assert math.isclose(0.1 + 0.2, 0.3)
    assert 0.1 + 0.2 == pytest.approx(0.3)


def test_nan_identity_shortcut() -> None:
    """NaN は自分と等しくないが、コンテナは is で短絡するので同じオブジェクトなら True。"""
    nan = math.nan
    assert nan != nan
    assert [nan] == [nan]
    assert {"a": nan} == {"a": nan}
    assert [nan] != [float("nan")]
    assert nan in [nan]
    assert float("nan") not in [nan]
    assert [nan].count(nan) == 1
    assert ([nan] != [nan]) is False


def test_scalars_of_different_types() -> None:
    """型の違うスカラーは False。キーの有無も区別する。"""
    assert "1" != 1
    assert "a" != b"a"
    assert None != 0  # noqa: E711
    assert None != False  # noqa: E711,E712
    assert {"a": None} != {}
    assert {"a": 1} != {"a": 1, "b": 2}


def test_dataclass_and_class_equality() -> None:
    """dataclass は同じクラスで全フィールド一致なら True、eq=False と素のクラスは同一性比較。"""

    @dataclasses.dataclass
    class P:
        x: int
        y: list

    @dataclasses.dataclass
    class Q:
        x: int
        y: list

    @dataclasses.dataclass(eq=False)
    class R:
        x: int

    class C:
        def __init__(self, x: int) -> None:
            self.x = x

    assert P(1, [1]) == P(1, [1])
    assert P(1, [1]) != Q(1, [1])
    assert P(1, [1]) != (1, [1])
    assert R(1) != R(1)
    assert C(1) != C(1)
    assert vars(C(1)) == vars(C(1))
    NT = namedtuple("NT", "x y")
    assert NT(1, 2) == (1, 2)


def test_datetime_and_functions() -> None:
    """naive / aware の datetime は False、date と datetime も False、関数は同じ参照のみ。"""
    naive = datetime.datetime(2020, 1, 1)
    aware = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    assert naive == datetime.datetime(2020, 1, 1)
    assert naive != aware
    assert datetime.date(2020, 1, 1) != naive

    def f() -> int:
        return 1

    assert {"f": f} == {"f": f}
    assert {"f": f} != {"f": lambda: 1}


def test_circular_structures() -> None:
    """別オブジェクトの循環構造同士は RecursionError、同じオブジェクトなら True。"""
    a: list = [1]
    a.append(a)
    b: list = [1]
    b.append(b)
    with pytest.raises(RecursionError):
        a == b  # noqa: B015
    assert a == a


def test_alternatives_for_order_insensitive_lists() -> None:
    """Alternatives: 順序を無視した list の比較。"""
    assert sorted([3, 1, 2]) == sorted([1, 2, 3])
    assert Counter([1, 1, 2]) == Counter([2, 1, 1])
    assert Counter([1, 1, 2]) != Counter([1, 2, 2])


def test_pitfalls_bool_int_keys_and_json_roundtrip() -> None:
    """Pitfalls: 1 / 1.0 / True はキーとして同一視され、JSON 往復で tuple と int キーが変わる。"""
    assert {1, 1.0, True} == {1}
    assert dict([(1, "a"), (1.0, "b"), (True, "c")]) == {1: "c"}
    assert {"ok": True} == {"ok": 1}
    assert type(True) is not type(1)
    assert json.loads(json.dumps({"t": (1, 2)})) != {"t": (1, 2)}
    assert json.loads(json.dumps({"t": (1, 2)})) == {"t": [1, 2]}
    assert json.loads(json.dumps({1: "a"})) == {"1": "a"}
