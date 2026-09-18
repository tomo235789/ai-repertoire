"""カード set-difference の Contract を検証するテスト"""

import pytest


def test_returns_new_set_without_mutating_operands():
    """a にあって b に無いものを新しい set で返し、a も b も変わらない"""
    a = {1, 2, 3, 4}
    b = {2, 4, 5}
    result = a - b
    assert result == {1, 3}
    assert result is not a
    assert b - a == {5}
    assert a.difference(b) == {1, 3}
    assert a == {1, 2, 3, 4}
    assert b == {2, 4, 5}


def test_related_operations():
    """対称差・共通部分・部分集合判定"""
    a = {1, 2, 3, 4}
    b = {2, 4, 5}
    assert a ^ b == {1, 3, 5}
    assert a.symmetric_difference(b) == {1, 3, 5}
    assert a & b == {2, 4}
    assert a.intersection(b) == {2, 4}
    assert {1, 2} <= a
    assert {1, 2}.issubset(a)
    assert a >= {1, 2}
    assert a.isdisjoint({7, 8})
    assert not a.isdisjoint(b)


def test_operator_requires_set_and_method_accepts_iterables():
    """演算子は set / frozenset 同士のみ。メソッドは任意のイテラブルを受け取る"""
    a = {1, 2, 3, 4}
    with pytest.raises(TypeError):
        a - [1]
    with pytest.raises(TypeError):
        a ^ [1]
    with pytest.raises(TypeError):
        a <= [1, 2, 3, 4]
    assert a - {1: "x"}.keys() == {2, 3, 4}
    assert a.difference([2, 4], [1]) == {3}
    assert a.difference(range(3)) == {3, 4}
    assert a.intersection([2, 4, 9]) == {2, 4}
    assert a.symmetric_difference([1, 9]) == {2, 3, 4, 9}
    with pytest.raises(TypeError):
        a.symmetric_difference([1], [2])
    assert {1, 2}.issubset(iter([1, 2, 3]))


def test_result_type_follows_left_operand():
    """frozenset - set は frozenset、set - frozenset は set"""
    assert type(frozenset([1, 2]) - {1}) is frozenset
    assert type({1, 2} - frozenset([1])) is set


def test_element_identity_uses_hash_and_equality():
    """1 と 1.0、1 と True は同じ要素"""
    assert {1} - {1.0} == set()
    assert {1, 2} - {True} == {2}


def test_empty_cases():
    """a が空、または b が a を含めば空。b が空なら a のコピー"""
    a = {1, 2}
    assert set() - a == set()
    assert a - {1, 2, 3} == set()
    copied = a - set()
    assert copied == a
    assert copied is not a


def test_strict_and_non_strict_subset():
    """< は真部分集合、<= は等しくても True。空集合はどの集合の部分集合でもある"""
    assert not {1, 2} < {1, 2}
    assert {1, 2} <= {1, 2}
    assert {1, 2} < {1, 2, 3}
    assert set() <= set()
    assert set() <= {1}
    assert not set() < set()


def test_in_place_operations_mutate():
    """-= と *_update は a 自身を書き換える"""
    a = {1, 2, 3}
    alias = a
    a -= {2}
    assert alias == {1, 3}
    a.difference_update([3])
    assert alias == {1}
    a.intersection_update([1, 9])
    assert alias == {1}
    a.symmetric_difference_update([1, 5])
    assert alias == {5}


def test_unhashable_element_raises_type_error():
    """ハッシュ不可な要素は TypeError"""
    with pytest.raises(TypeError):
        {1}.difference([[1]])


def test_list_difference_and_dict_keys_alternatives():
    """Alternatives: リストの差は順序と重複を保つ。dict.keys() 同士の差は set"""
    xs = [3, 1, 3, 2]
    excluded = {1}
    assert [x for x in xs if x not in excluded] == [3, 3, 2]
    result = {"a": 1, "b": 2}.keys() - {"a": 0}.keys()
    assert result == {"b"}
    assert type(result) is set
