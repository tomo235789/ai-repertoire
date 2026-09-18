"""カード map-group-to-map の Contract を検証するテスト"""

import json
from collections import defaultdict
from itertools import groupby

import pytest


def group_by(iterable, key):
    d = defaultdict(list)
    for x in iterable:
        d[key(x)].append(x)
    return d


def test_keeps_element_order_and_key_first_seen_order():
    """各グループは出現順、キーは初出順に並ぶ"""
    result = group_by(["apple", "bob", "cat", "dove"], len)
    assert dict(result) == {5: ["apple"], 3: ["bob", "cat"], 4: ["dove"]}
    assert list(result) == [5, 3, 4]


def test_is_eager_and_key_is_called_once_per_element_in_order():
    """入力を読み切り、key は各要素につき 1 回、先頭から順に呼ばれる"""
    calls = []

    def key(n):
        calls.append(n)
        return n % 2

    group_by([1, 2, 1], key)
    assert calls == [1, 2, 1]


def test_does_not_mutate_input_and_keeps_references():
    """入力を変更せず、返り値は defaultdict で要素は同じ参照"""
    a = {"k": 1}
    src = [a, {"k": 2}]
    result = group_by(src, lambda o: o["k"])
    assert src == [{"k": 1}, {"k": 2}]
    assert isinstance(result, defaultdict)
    assert result[1][0] is a


def test_key_identity_uses_hash_and_equality():
    """1 と 1.0 と True は同じグループ、1 と '1' は別グループ。タプルや None もキーにできる"""
    assert dict(group_by([1, 1.0, True, "1"], lambda x: x)) == {1: [1, 1.0, True], "1": ["1"]}
    assert dict(group_by([(1, 2), (1, 2)], lambda x: x)) == {(1, 2): [(1, 2), (1, 2)]}
    assert dict(group_by([None], lambda x: x)) == {None: [None]}


def test_unhashable_key_raises_type_error():
    """ハッシュ不可なキーは TypeError"""
    with pytest.raises(TypeError):
        group_by([[1]], lambda x: x)


def test_empty_input_and_conversion_to_dict():
    """空なら空の defaultdict。dict() で戻せて == は内容で比較される"""
    result = group_by([], len)
    assert isinstance(result, defaultdict)
    assert result == {}
    plain = dict(group_by([1, 2], lambda x: x % 2))
    assert type(plain) is dict
    assert plain == {1: [1], 0: [2]}


def test_missing_key_is_inserted_on_read_but_not_with_get():
    """d[missing] は [] を返しつつ挿入する。get は挿入しない"""
    d = group_by([1], lambda x: x)
    assert d[99] == []
    assert 99 in d
    assert d.get(100) is None
    assert 100 not in d
    plain = dict(d)
    with pytest.raises(KeyError):
        plain[100]


def test_json_dumps_stringifies_keys():
    """Pitfalls: json.dumps でキーが文字列化される"""
    assert json.dumps(dict(group_by([5], lambda x: x))) == '{"5": [5]}'


def test_itertools_groupby_only_groups_adjacent_elements():
    """Alternatives: itertools.groupby は連続した要素しかまとめない"""
    unsorted = [(k, list(g)) for k, g in groupby([1, 2, 1])]
    assert unsorted == [(1, [1]), (2, [2]), (1, [1])]
    presorted = [(k, list(g)) for k, g in groupby(sorted([1, 2, 1]))]
    assert presorted == [(1, [1, 1]), (2, [2])]
