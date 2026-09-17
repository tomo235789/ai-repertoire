"""カード collection-zip の Contract を検証するテスト"""

from itertools import count, zip_longest

import pytest


def test_pairs_elements_by_position_in_order():
    """i 番目のタプルは各入力の i 番目の要素からなる"""
    assert list(zip([1, 2, 3], ["a", "b", "c"])) == [(1, "a"), (2, "b"), (3, "c")]


def test_does_not_mutate_input_and_keeps_references():
    """入力を変更せず、各タプルは新しく作られ要素は同じ参照"""
    a = {"k": 1}
    left = [a]
    right = [2]
    result = list(zip(left, right))
    assert left == [{"k": 1}] and right == [2]
    assert isinstance(result[0], tuple)
    assert result[0][0] is a


def test_is_lazy_and_single_pass():
    """タプル 1 つ分ずつ読み進め、2 回目の走査は空になる"""
    assert next(zip(count(), "ab")) == (0, "a")
    once = zip([1, 2], [3, 4])
    assert list(once) == [(1, 3), (2, 4)]
    assert list(once) == []


def test_truncates_to_shortest_and_consumes_one_extra_from_earlier_args():
    """最短で打ち切る。尽きた入力より前の引数からは 1 要素余分に消費される"""
    assert list(zip([1, 2, 3], ["a", "b"])) == [(1, "a"), (2, "b")]

    earlier = iter([1, 2, 3, 4])
    assert list(zip(earlier, [1])) == [(1, 1)]
    assert list(earlier) == [3, 4]

    later = iter([1, 2, 3, 4])
    assert list(zip([1], later)) == [(1, 1)]
    assert list(later) == [2, 3, 4]


def test_strict_raises_on_length_mismatch():
    """strict=True で長さが揃わなければ ValueError"""
    with pytest.raises(ValueError):
        list(zip([1, 2, 3], ["a", "b"], strict=True))
    assert list(zip([1, 2], ["a", "b"], strict=True)) == [(1, "a"), (2, "b")]


def test_variadic_and_empty_inputs():
    """タプル長は引数の数。引数なし・いずれかが空なら何も返さない"""
    assert list(zip([1, 2], [3, 4], [5, 6])) == [(1, 3, 5), (2, 4, 6)]
    assert list(zip([1, 2])) == [(1,), (2,)]
    assert list(zip()) == []
    assert list(zip([], [1, 2])) == []


def test_zip_longest_fills_missing_positions():
    """Alternatives: zip_longest は最長に合わせて fillvalue で埋める"""
    assert list(zip_longest([1, 2, 3], ["a"], fillvalue=None)) == [(1, "a"), (2, None), (3, None)]
