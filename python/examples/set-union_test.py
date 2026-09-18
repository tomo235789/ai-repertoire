"""カード set-union の Contract を検証するテスト"""

from functools import reduce

import pytest


def test_returns_new_set_without_mutating_operands():
    """新しい set を返し、a も引数も変わらない"""
    a = {3, 1, 2}
    b = {2, 4, 1}
    result = a | b
    assert result == {1, 2, 3, 4}
    assert result is not a
    assert a == {3, 1, 2}
    assert b == {2, 4, 1}
    assert a.union(b) == {1, 2, 3, 4}
    copied = a.union()
    assert copied == a
    assert copied is not a


def test_operator_requires_set_and_method_accepts_any_iterables():
    """| は set / frozenset 同士のみ。union() は任意のイテラブルを複数受け取れる"""
    a = {1, 2}
    with pytest.raises(TypeError):
        a | [3]
    with pytest.raises(TypeError):
        a | {3: "x"}
    assert a | {3: "x"}.keys() == {1, 2, 3}
    assert a.union([3, 4], range(5, 7), (x for x in [7]), "x", {8: "y"}) == {1, 2, 3, 4, 5, 6, 7, "x", 8}


def test_result_type_follows_left_operand():
    """frozenset | set は frozenset、set | frozenset は set。サブクラスでも返り値は set"""
    assert type(frozenset([1]) | {2}) is frozenset
    assert type({1} | frozenset([2])) is set
    assert type(frozenset([1]).union([2])) is frozenset

    class MySet(set):
        pass

    assert type(MySet([1]) | MySet([2])) is set
    assert type(MySet([1]).union([2])) is set


def test_element_identity_uses_hash_and_equality():
    """1 と 1.0、0 と False は同じ要素"""
    assert {1} | {1.0} == {1}
    assert len({0} | {False}) == 1
    assert {1} | {"1"} == {1, "1"}


def test_empty_sets():
    """空同士なら空。片方が空なら他方のコピー"""
    assert set() | set() == set()
    assert {1, 2} | set() == {1, 2}
    assert set().union([1, 2]) == {1, 2}
    assert set().union(*[]) == set()


def test_unhashable_or_non_iterable_raises_type_error():
    """ハッシュ不可な要素やイテラブルでない引数は TypeError"""
    with pytest.raises(TypeError):
        {1}.union([[1]])
    with pytest.raises(TypeError):
        {1}.union(1)


def test_in_place_union_mutates():
    """|= と update は a 自身に追加する"""
    a = {1}
    alias = a
    a |= {2}
    assert alias == {1, 2}
    a.update([3], (4,))
    assert alias == {1, 2, 3, 4}


def test_union_of_many_sets():
    """Alternatives: set().union(*sets) と reduce で複数の set をまとめる"""
    sets = [{1}, {2}, {3}]
    assert set().union(*sets) == {1, 2, 3}
    assert reduce(set.union, sets, set()) == {1, 2, 3}


def test_string_argument_is_split_into_characters():
    """Pitfalls: union("ab") は 1 文字ずつ。文字列 1 つは {"ab"} で渡す"""
    assert {1}.union("ab") == {1, "a", "b"}
    assert {1} | {"ab"} == {1, "ab"}
