"""カード iter-lazy-map の Contract を検証するテスト"""

from itertools import count, islice

import pytest


def test_is_lazy_and_calls_function_once_per_pulled_element():
    """map を呼んだ時点では関数は呼ばれず、取り出した要素につき 1 回、先頭から順に呼ばれる"""
    calls = []

    def double(n):
        calls.append(n)
        return n * 2

    m = map(double, [1, 2, 3])
    assert calls == []
    assert next(m) == 2
    assert calls == [1]
    assert list(m) == [4, 6]
    assert calls == [1, 2, 3]


def test_returns_iterator_not_list():
    """返り値はイテレータで、iter(m) is m。len や添字は使えない"""
    m = map(str, [1, 2])
    assert iter(m) is m
    with pytest.raises(TypeError):
        len(m)
    assert list(m) == ["1", "2"]


def test_does_not_mutate_input_and_is_single_pass():
    """入力を変更せず、消費し切った後にもう一度走査すると空になる"""
    src = [1, 2, 3]
    m = map(lambda x: x * 10, src)
    assert list(m) == [10, 20, 30]
    assert list(m) == []
    assert src == [1, 2, 3]


def test_works_on_infinite_iterator_with_islice():
    """無限イテレータでも islice で区切れば先頭だけ計算される"""
    assert list(islice(map(lambda n: n * n, count()), 3)) == [0, 1, 4]


def test_multiple_iterables_stop_at_shortest_and_overconsume_earlier_args():
    """複数イテラブルは最短で打ち切り、尽きた入力より前の引数から 1 要素余分に消費する"""
    assert list(map(pow, [2, 3], [3, 2])) == [8, 9]
    first = iter([1, 2, 3])
    second = iter([10])
    assert list(map(lambda a, b: a + b, first, second)) == [11]
    assert list(first) == [3]


def test_empty_input_yields_nothing():
    """空のイテラブルからは空のイテレータが返る"""
    assert list(map(str, [])) == []


def test_non_callable_raises_on_first_next_not_on_call():
    """function が呼び出し可能でなくても map() は通り、最初の next() で TypeError"""
    m = map(1, [1])
    with pytest.raises(TypeError):
        next(m)


def test_missing_or_non_iterable_argument_raises_on_call():
    """イテラブルを渡さない、またはイテラブルでないものを渡すと呼んだ時点で TypeError"""
    with pytest.raises(TypeError):
        map(str)
    with pytest.raises(TypeError):
        map(str, 1)
