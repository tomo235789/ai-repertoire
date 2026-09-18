"""json-stringify-stable: json.dumps(sort_keys=True, separators=(",", ":")) の Contract を検証する。"""

import dataclasses
import datetime
import enum
import hashlib
import json
import math
from collections import OrderedDict
from decimal import Decimal

import pytest


def stable(obj: object, **kwargs: object) -> str:
    """キー順を揃え、空白を落とした JSON 文字列を返す。"""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, **kwargs)


def test_sorts_keys_at_every_level_and_keeps_list_order() -> None:
    """全階層のキーをソートし、リストの順序は変えない。"""
    assert stable({"b": 1, "a": {"d": 2, "c": 3}}) == '{"a":{"c":3,"d":2},"b":1}'
    assert stable([{"b": 1, "a": 2}, [3, 1, 2]]) == '[{"a":2,"b":1},[3,1,2]]'
    assert stable({"b": 1, "a": 2}) == stable({"a": 2, "b": 1})
    assert stable(OrderedDict([("b", 1), ("a", 2)])) == '{"a":2,"b":1}'
    assert json.dumps({"b": 1, "a": 2}) == '{"b": 1, "a": 2}'


def test_key_ordering_is_by_original_value() -> None:
    """文字列キーはコードポイント順、int キーは数値順。"""
    assert stable({"b": 1, "B": 2, "あ": 3, "a": 4, "_": 5, "1": 6, "10": 7, "2": 8}) == (
        '{"1":6,"10":7,"2":8,"B":2,"_":5,"a":4,"b":1,"あ":3}'
    )
    assert stable({10: "b", 2: "a"}) == '{"2":"a","10":"b"}'
    assert stable({"10": "b", "2": "a"}) == '{"10":"b","2":"a"}'


def test_non_string_keys() -> None:
    """True / None / int / float キーは文字列化され、tuple は TypeError、混在は sort_keys で TypeError。"""
    assert json.dumps({True: 1, None: 2, 3: 4, 1.5: 5}) == '{"true": 1, "null": 2, "3": 4, "1.5": 5}'
    with pytest.raises(TypeError):
        json.dumps({(1, 2): 1})
    assert json.dumps({(1, 2): 1, "a": 2}, skipkeys=True) == '{"a": 2}'
    with pytest.raises(TypeError):
        stable({1: "a", "1": "b"})
    with pytest.raises(TypeError):
        stable({None: 1, 2: 2})
    assert json.dumps({1: "a", "1": "b"}) == '{"1": "a", "1": "b"}'


def test_separators_indent_and_ensure_ascii() -> None:
    """separators で空白を無くし、indent は別の文字列になり、ensure_ascii は非 ASCII の出方を変える。"""
    assert json.dumps({"a": 1, "b": [1, 2]}, separators=(",", ":")) == '{"a":1,"b":[1,2]}'
    assert json.dumps({"b": 1, "a": 2}, sort_keys=True, indent=2) == '{\n  "a": 2,\n  "b": 1\n}'
    assert json.dumps({"名": "値"}) == '{"\\u540d": "\\u5024"}'
    assert stable({"名": "値"}) == '{"名":"値"}'


def test_value_mapping() -> None:
    """None / bool / tuple / 大きな int / float / IntEnum の出方。"""

    class Level(enum.IntEnum):
        ONE = 1

    assert stable({"n": None, "b": True, "t": (1, 2), "i": 10**20, "f": 1.0, "e": 1e16, "l": Level.ONE}) == (
        '{"b":true,"e":1e+16,"f":1.0,"i":100000000000000000000,"l":1,"n":null,"t":[1,2]}'
    )
    assert stable({"f": 0.1 + 0.2}) == '{"f":0.30000000000000004}'


def test_unserializable_types_and_default() -> None:
    """date / Decimal / set / bytes / dataclass / Enum は TypeError で、default で変換できる。"""

    class Color(enum.Enum):
        RED = "red"

    @dataclasses.dataclass
    class Point:
        x: int

    for value in (datetime.date(2020, 1, 1), Decimal("1.10"), {1}, b"x", Point(1), Color.RED):
        with pytest.raises(TypeError, match="is not JSON serializable"):
            json.dumps(value)

    def convert(obj: object) -> object:
        if isinstance(obj, datetime.date):
            return obj.isoformat()
        if isinstance(obj, set):
            return sorted(obj)
        raise TypeError(f"not serializable: {type(obj).__name__}")

    assert stable({"s": {3, 1, 2}, "at": datetime.date(2020, 1, 1)}, default=convert) == (
        '{"at":"2020-01-01","s":[1,2,3]}'
    )
    assert stable({"at": datetime.date(2020, 1, 1), "n": Decimal("1.10")}, default=str) == (
        '{"at":"2020-01-01","n":"1.10"}'
    )
    with pytest.raises(TypeError, match="not serializable: object"):
        stable({"x": object()}, default=convert)


def test_circular_reference_raises_and_shared_refs_expand() -> None:
    """循環参照は ValueError、同じオブジェクトへの複数参照は展開される。"""
    cyclic: dict = {"a": 1}
    cyclic["self"] = cyclic
    with pytest.raises(ValueError, match="Circular reference detected"):
        json.dumps(cyclic)
    shared = {"k": 1}
    assert stable({"x": shared, "y": shared}) == '{"x":{"k":1},"y":{"k":1}}'


def test_nan_and_infinity() -> None:
    """nan / inf は既定で NaN / Infinity として出て、allow_nan=False で ValueError。"""
    assert json.dumps({"n": math.nan, "i": math.inf, "m": -math.inf}) == '{"n": NaN, "i": Infinity, "m": -Infinity}'
    with pytest.raises(ValueError, match="Out of range float values are not JSON compliant"):
        json.dumps({"n": math.nan}, allow_nan=False)


def test_hash_is_stable_across_insertion_order() -> None:
    """Alternatives: ハッシュに使うと挿入順によらず同じ値になる。"""
    a = hashlib.sha256(stable({"b": 1, "a": [1, {"d": 2, "c": 3}]}).encode()).hexdigest()
    b = hashlib.sha256(stable({"a": [1, {"c": 3, "d": 2}], "b": 1}).encode()).hexdigest()
    assert a == b
    assert hashlib.sha256(json.dumps({"b": 1, "a": 2}).encode()).hexdigest() != (
        hashlib.sha256(json.dumps({"a": 2, "b": 1}).encode()).hexdigest()
    )
