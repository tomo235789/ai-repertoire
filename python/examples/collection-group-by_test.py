"""カード collection-group-by の Contract を検証するテスト"""

from collections import defaultdict
from itertools import groupby

import pytest
from more_itertools import map_reduce


def test_keeps_element_order_and_key_first_seen_order():
    """各グループは出現順、キーも初出順に並ぶ"""
    result = map_reduce(["b", "a", "bb", "c"], keyfunc=len)
    assert result == {1: ["b", "a", "c"], 2: ["bb"]}
    assert list(result) == [1, 2]


def test_does_not_mutate_input_and_returns_plain_defaultdict():
    """入力を変更せず、要素は同じ参照。default_factory は None で未知キーは KeyError"""
    a = {"k": 1}
    src = [a, {"k": 2}]
    result = map_reduce(src, keyfunc=lambda o: o["k"])
    assert src == [{"k": 1}, {"k": 2}]
    assert result[1][0] is a
    assert isinstance(result, defaultdict)
    assert result.default_factory is None
    with pytest.raises(KeyError):
        result[99]
    assert result.get(99, []) == []


def test_is_eager():
    """返る時点で入力をすべて読み終えている"""
    seen = []

    def gen():
        for i in range(3):
            seen.append(i)
            yield i

    map_reduce(gen(), keyfunc=lambda x: x % 2)
    assert seen == [0, 1, 2]


def test_keyfunc_is_called_once_per_element_in_order():
    """keyfunc は各要素につき 1 回、先頭から順に呼ばれる"""
    seen = []

    def key(n):
        seen.append(n)
        return n % 2

    map_reduce([1, 2, 1], keyfunc=key)
    assert seen == [1, 2, 1]


def test_key_comparison_uses_hash_and_equality():
    """1 と 1.0 は同じグループ、1 と '1' は別グループ"""
    assert dict(map_reduce([1, 1.0, "1"], keyfunc=lambda x: x)) == {1: [1, 1.0], "1": ["1"]}


def test_valuefunc_and_reducefunc():
    """valuefunc で値を変換し、reducefunc でグループを集約できる"""
    counts = map_reduce([1, 2, 3, 4, 5], keyfunc=lambda x: x % 2, reducefunc=len)
    assert counts == {1: 3, 0: 2}
    joined = map_reduce([1, 2, 3], keyfunc=lambda x: x % 2, valuefunc=str, reducefunc=",".join)
    assert joined == {1: "1,3", 0: "2"}


def test_empty_input_returns_empty_defaultdict():
    """空のイテラブルは空の defaultdict を返す"""
    result = map_reduce([], keyfunc=len)
    assert isinstance(result, defaultdict)
    assert result == {}


def test_unhashable_key_raises_type_error():
    """ハッシュ不可なキーは TypeError"""
    with pytest.raises(TypeError):
        map_reduce([[1]], keyfunc=lambda x: x)


def test_itertools_groupby_only_groups_adjacent_elements():
    """Alternatives: itertools.groupby は連続した要素しかまとめない"""
    unsorted = [(k, list(g)) for k, g in groupby([1, 2, 1], key=lambda x: x)]
    assert unsorted == [(1, [1]), (2, [2]), (1, [1])]
    presorted = [(k, list(g)) for k, g in groupby(sorted([1, 2, 1]), key=lambda x: x)]
    assert presorted == [(1, [1, 1]), (2, [2])]
