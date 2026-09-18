"""カード iter-lazy-filter の Contract を検証するテスト"""

from itertools import count, filterfalse, islice

import pytest


def test_is_lazy_and_calls_predicate_once_per_scanned_element():
    """filter を呼んだ時点では述語は呼ばれず、next() のたびに真の要素が見つかるまで進める"""
    calls = []

    def is_big(n):
        calls.append(n)
        return n > 1

    f = filter(is_big, [1, 2, 3])
    assert calls == []
    assert next(f) == 2
    assert calls == [1, 2]
    assert list(f) == [3]
    assert calls == [1, 2, 3]


def test_keeps_order_and_references():
    """順序を保ち、要素は同じ参照のまま流れる"""
    a = {"k": 1}
    b = {"k": 2}
    result = list(filter(lambda o: o["k"] > 0, [a, b]))
    assert result[0] is a
    assert result[1] is b


def test_predicate_result_is_truthy_checked():
    """述語の返り値は truthy 判定。0 / '' / None / 空リストを返した要素は落ちる"""
    assert list(filter(lambda x: 0, [1])) == []
    assert list(filter(lambda x: [], [1])) == []
    assert list(filter(lambda x: "x", [1])) == [1]
    assert list(filter(lambda s: s.find("a"), ["abc", "bad"])) == ["bad"]


def test_none_predicate_uses_element_truthiness():
    """None を渡すと要素自身の真偽値で絞る"""
    assert list(filter(None, [0, 1, "", "a", None, [], [0]])) == [1, "a", [0]]
    assert list(filterfalse(None, [0, 1, "", "a", None])) == [0, "", None]


def test_is_single_pass_and_does_not_mutate_input():
    """消費し切った後にもう一度走査すると空。入力は変わらない"""
    src = [1, 2, 3, 4]
    f = filter(lambda n: n % 2 == 0, src)
    assert list(f) == [2, 4]
    assert list(f) == []
    assert src == [1, 2, 3, 4]


def test_works_on_infinite_iterator_with_islice():
    """無限イテレータでも islice で区切れば必要な分しか判定されない"""
    assert list(islice(filter(lambda n: n % 3 == 0, count()), 3)) == [0, 3, 6]


def test_empty_input_yields_nothing():
    """空のイテラブルからは空のイテレータが返る"""
    assert list(filter(None, [])) == []


def test_non_callable_raises_on_first_next_and_non_iterable_raises_on_call():
    """述語が不正なら最初の next() で TypeError、イテラブルでなければ呼んだ時点で TypeError"""
    f = filter(1, [1])
    with pytest.raises(TypeError):
        next(f)
    with pytest.raises(TypeError):
        filter(None, 1)
