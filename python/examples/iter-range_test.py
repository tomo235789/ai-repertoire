"""カード iter-range の Contract を検証するテスト"""

import sys

import pytest


def test_basic_forms():
    """引数 1 つは 0 始まり、start / stop / step を指定でき、負の step で降順"""
    assert list(range(4)) == [0, 1, 2, 3]
    assert list(range(1, 4)) == [1, 2, 3]
    assert list(range(0, 20, 5)) == [0, 5, 10, 15]
    assert list(range(0, -4, -1)) == [0, -1, -2, -3]


def test_unreachable_stop_is_empty():
    """step で届かなければ空。range(0) や range(-3) も空"""
    assert list(range(5, 1)) == []
    assert list(range(0)) == []
    assert list(range(-3)) == []
    assert list(range(1, 5, -1)) == []


def test_is_lazy_and_constant_memory():
    """要素を持たず、巨大な範囲でもメモリは一定で in は即座に返る"""
    big = range(10**18)
    assert sys.getsizeof(big) == sys.getsizeof(range(3))
    assert 10**17 in big  # 実行時間は環境依存なので測らない（O(1) 判定であることは公式仕様）
    assert big[-1] == 10**18 - 1


def test_is_reusable_sequence_with_len_index_slice_and_reversed():
    """何度でも走査でき、len / 添字 / in / index / count / スライス / reversed が使える"""
    r = range(0, 20, 5)
    assert list(r) == [0, 5, 10, 15]
    assert list(r) == [0, 5, 10, 15]
    assert len(r) == 4
    assert r[1] == 5
    assert r[-1] == 15
    assert 10 in r
    assert 3 not in r
    assert r.index(15) == 3
    assert r.count(5) == 1
    assert r[1:3] == range(5, 15, 5)
    assert list(reversed(r)) == [15, 10, 5, 0]


def test_invalid_arguments_raise():
    """小数は TypeError、step 0 は ValueError、範囲外の添字は IndexError、無い値の index は ValueError"""
    with pytest.raises(TypeError):
        range(1.5)
    with pytest.raises(TypeError):
        range(0, 2.5)
    with pytest.raises(ValueError):
        range(0, 3, 0)
    with pytest.raises(IndexError):
        range(3)[5]
    with pytest.raises(ValueError):
        range(3).index(5)


def test_equality_compares_the_sequence():
    """同じ列を表す range は等しく、リストとは等しくない"""
    assert range(0, 3) == range(3)
    assert range(0) == range(5, 1)
    assert range(0, 10, 2) == range(0, 9, 2)
    assert range(3) != [0, 1, 2]


def test_float_membership_uses_equality():
    """Pitfalls: 1.0 in range(3) は True"""
    assert 1.0 in range(3)
    assert 1.5 not in range(3)
