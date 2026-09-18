"""json-clone: copy.deepcopy の Contract を検証する。"""

import copy
import dataclasses
import datetime
import enum
import json
import re
import threading
from collections import OrderedDict, defaultdict

import pytest


def test_copies_every_level_and_keeps_source() -> None:
    """可変なコンテナを全階層で新しく作り、元の値は変更しない。型も保つ。"""
    src = {"tags": {"a"}, "nested": {"n": [1, 2]}, "t": (1, [2])}
    dup = copy.deepcopy(src)
    dup["nested"]["n"].append(3)
    dup["tags"].add("b")
    dup["t"][1].append(9)
    assert src == {"tags": {"a"}, "nested": {"n": [1, 2]}, "t": (1, [2])}
    assert dup["nested"] is not src["nested"]
    assert dup["t"] is not src["t"]
    assert type(copy.deepcopy(OrderedDict(a=1))) is OrderedDict
    dd = copy.deepcopy(defaultdict(list, a=[1]))
    assert type(dd) is defaultdict
    assert dd.default_factory is list

    class MyDict(dict):
        pass

    assert type(copy.deepcopy(MyDict(a=[1]))) is MyDict


def test_immutables_share_reference() -> None:
    """不変な値は同じ参照、frozenset と date は新しいオブジェクト。"""

    class Color(enum.Enum):
        RED = 1

    shared = {"s": "abc", "i": 10**30, "f": 1.5, "b": b"x", "n": None, "t": (1, 2), "r": re.compile("x"), "e": Color.RED}
    dup = copy.deepcopy(shared)
    for key in shared:
        assert dup[key] is shared[key], key
    assert copy.deepcopy((1, [2])) is not (t := (1, [2])) and copy.deepcopy(t) == t
    fs = frozenset({1})
    assert copy.deepcopy(fs) is not fs
    assert copy.deepcopy(fs) == fs
    when = datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc)
    assert copy.deepcopy(when) is not when
    assert copy.deepcopy(when) == when


def test_circular_and_shared_references() -> None:
    """循環参照と同じオブジェクトへの複数参照は複製後も構造を保つ。"""
    cyclic: dict = {"a": 1}
    cyclic["self"] = cyclic
    dup = copy.deepcopy(cyclic)
    assert dup is not cyclic
    assert dup["self"] is dup
    inner = {"k": 1}
    two = copy.deepcopy({"x": inner, "y": inner})
    assert two["x"] is two["y"]
    assert two["x"] is not inner


def test_class_instances_keep_class_and_methods() -> None:
    """クラスインスタンスは同じクラスの新しいインスタンスで、メソッドも保たれる。"""

    class Bag:
        __slots__ = ("items",)

        def __init__(self, items: list) -> None:
            self.items = items

        def size(self) -> int:
            return len(self.items)

    @dataclasses.dataclass
    class P:
        x: int
        y: list

    bag = Bag([1, 2])
    dup = copy.deepcopy(bag)
    assert type(dup) is Bag
    assert dup.size() == 2
    assert dup.items is not bag.items
    p = P(1, [2])
    pc = copy.deepcopy(p)
    pc.y.append(3)
    assert p == P(1, [2])
    assert pc == P(1, [2, 3])


def test_functions_are_shared_and_unpicklable_raise() -> None:
    """関数 / クラス / 組み込みは同じ参照、モジュール / ジェネレータ / ロック / ファイルは TypeError。"""

    def fn() -> int:
        return 1

    src = {"fn": fn, "cls": dict, "builtin": len, "meth": "".join}
    dup = copy.deepcopy(src)
    for key in src:
        assert dup[key] is src[key], key
    with pytest.raises(TypeError, match="cannot pickle"):
        copy.deepcopy({"mod": json})
    with pytest.raises(TypeError, match="cannot pickle"):
        copy.deepcopy((i for i in range(3)))
    with pytest.raises(TypeError, match="cannot pickle"):
        copy.deepcopy({"lock": threading.Lock()})
    with open(__file__) as f, pytest.raises(TypeError, match="cannot pickle"):
        copy.deepcopy({"file": f})


def test_deepcopy_hook_and_memo() -> None:
    """__deepcopy__ で複製の仕方を決められ、memo で共有参照を引き継ぐ。"""

    class Handle:
        def __init__(self, conn: object, buf: list) -> None:
            self.conn = conn
            self.buf = buf

        def __deepcopy__(self, memo: dict) -> "Handle":
            return Handle(self.conn, copy.deepcopy(self.buf, memo))

    class Keep:
        def __deepcopy__(self, memo: dict) -> "Keep":
            return self

    conn = object()
    handle = Handle(conn, [1])
    dup = copy.deepcopy(handle)
    assert dup.conn is conn
    assert dup.buf == [1] and dup.buf is not handle.buf
    keep = Keep()
    assert copy.deepcopy({"k": keep})["k"] is keep

    shared = [1]
    memo: dict = {}
    first = copy.deepcopy(shared, memo)
    second = copy.deepcopy(shared, memo)
    assert first is second
    assert id(shared) in memo
    assert copy.deepcopy(shared, {id(shared): shared}) is shared


def test_deep_nesting_raises_recursion_error() -> None:
    """ネストが深すぎると RecursionError。"""
    deep: list = []
    cur = deep
    for _ in range(2000):
        nxt: list = []
        cur.append(nxt)
        cur = nxt
    with pytest.raises(RecursionError):
        copy.deepcopy(deep)


def test_shallow_copy_shares_nested_values() -> None:
    """Alternatives: copy.copy / dict(d) は浅いコピーで、ネストした値は共有される。"""
    src = {"nested": {"n": [1]}, "list": [1]}
    for shallow in (copy.copy(src), dict(src), {**src}):
        assert shallow is not src
        assert shallow["nested"] is src["nested"]
    copy.copy(src)["nested"]["n"].append(2)
    assert src["nested"]["n"] == [1, 2]
    rows = [[1], [2]]
    list(rows)[0].append(9)
    assert rows == [[1, 9], [2]]


def test_json_roundtrip_loses_types() -> None:
    """Alternatives: json.loads(json.dumps()) は tuple と int キーが変わり、date / set は TypeError。"""
    assert json.loads(json.dumps({"t": (1, 2), "k": {1: "a"}})) == {"t": [1, 2], "k": {"1": "a"}}
    with pytest.raises(TypeError):
        json.dumps({"d": datetime.date(2020, 1, 1)})
    with pytest.raises(TypeError):
        json.dumps({"s": {1}})


def test_exceptions_are_copied() -> None:
    """Pitfalls: 例外オブジェクトも複製され、args は同じ。"""
    err = ValueError("x")
    dup = copy.deepcopy(err)
    assert dup is not err
    assert type(dup) is ValueError
    assert dup.args == ("x",)
