"""カード iter-take の Contract を検証するテスト"""

from itertools import count, islice

import pytest


def test_takes_first_n_from_infinite_iterator():
    """無限イテレータから先頭 n 個だけ取り出す"""
    assert list(islice(count(), 3)) == [0, 1, 2]


def test_is_lazy_and_pulls_only_up_to_stop():
    """islice を呼んだ時点では元を進めず、stop を超える要素は元から取り出さない"""
    seen = []

    def gen():
        for i in range(10):
            seen.append(i)
            yield i

    s = islice(gen(), 3)
    assert seen == []
    assert next(s) == 0
    assert seen == [0]
    assert list(s) == [1, 2]
    assert seen == [0, 1, 2]
    assert list(islice(gen(), 0)) == []


def test_start_stop_step():
    """start 番目から stop 番目の手前まで、step 個おき。stop が None なら最後まで"""
    assert list(islice(count(), 5, 7)) == [5, 6]
    assert list(islice(count(), 0, 10, 3)) == [0, 3, 6, 9]
    assert list(islice([1, 2, 3, 4], 1, None)) == [2, 3, 4]
    assert list(islice([1, 2, 3, 4], None, None, 2)) == [1, 3]
    assert list(islice([1, 2, 3], 2, 1)) == []


def test_shorter_source_ends_early():
    """元が stop より短ければあるだけ返して終わる"""
    assert list(islice([1, 2], 5)) == [1, 2]
    assert list(islice([], 5)) == []


def test_consumes_source_and_source_continues_afterwards():
    """消費した要素は元に戻らず、islice の後は続きから読める。元は閉じられない"""
    it = iter(range(10))
    assert list(islice(it, 3)) == [0, 1, 2]
    assert next(it) == 3
    assert list(islice(it, 3)) == [4, 5, 6]

    closed = []

    def gen():
        try:
            yield from range(5)
        finally:
            closed.append(True)

    g = gen()
    assert list(islice(g, 2)) == [0, 1]
    assert closed == []
    assert next(g) == 2


def test_is_single_pass():
    """返り値は使い捨てで、消費し切った後は空"""
    s = islice([1, 2, 3], 2)
    assert list(s) == [1, 2]
    assert list(s) == []


def test_negative_or_non_integer_arguments_raise_on_call():
    """負数・非整数・step 0 以下は呼んだ時点で ValueError"""
    with pytest.raises(ValueError):
        islice([1, 2, 3], -1)
    with pytest.raises(ValueError):
        islice([1, 2, 3], 1, -1)
    with pytest.raises(ValueError):
        islice([1, 2, 3], 1.5)
    with pytest.raises(ValueError):
        islice([1, 2, 3], 0, 3, 0)
    with pytest.raises(ValueError):
        islice([1, 2, 3], 0, 3, -1)
