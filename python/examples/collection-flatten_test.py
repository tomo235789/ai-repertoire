"""カード collection-flatten の Contract を検証するテスト"""

from itertools import chain, count

import pytest
from more_itertools import collapse


def test_flattens_one_level_in_order():
    """外側・内側の順序を保って 1 段だけ開く"""
    assert list(chain.from_iterable([[1, 2], [3], [4, [5]]])) == [1, 2, 3, 4, [5]]


def test_does_not_mutate_input_and_keeps_references():
    """入力を変更せず、要素（残る内側の配列も）は同じ参照"""
    inner = [1]
    src = [[inner], [2]]
    result = list(chain.from_iterable(src))
    assert src == [[[1]], [2]]
    assert result[0] is inner


def test_is_lazy_and_single_pass():
    """取り出した分だけ読み進め、2 回目の走査は空になる"""
    assert next(chain.from_iterable([i] for i in count())) == 0
    once = chain.from_iterable([[1], [2]])
    assert list(once) == [1, 2]
    assert list(once) == []


def test_accepts_mixed_iterables_including_strings():
    """内側はイテラブルなら何でもよく、文字列は文字に分解される"""
    assert list(chain.from_iterable([(1, 2), {3}, "ab", range(2)])) == [1, 2, 3, "a", "b", 0, 1]
    assert list(chain.from_iterable(["ab", "cd"])) == ["a", "b", "c", "d"]


def test_empty_inputs_yield_nothing():
    """空、または空のイテラブルだけなら何も返さない"""
    assert list(chain.from_iterable([])) == []
    assert list(chain.from_iterable([[], []])) == []


def test_non_iterable_inner_raises_type_error_when_reached():
    """イテラブルでない要素に達した時点で TypeError"""
    it = chain.from_iterable([[1], 2])
    assert next(it) == 1
    with pytest.raises(TypeError):
        next(it)


def test_collapse_keeps_strings_and_can_limit_depth():
    """Alternatives: collapse は文字列を開かず、levels で深さを指定できる"""
    assert list(collapse(["ab", ["cd", ["ef"]]], levels=1)) == ["ab", "cd", ["ef"]]
    assert list(collapse(["ab", ["cd", ["ef"]]])) == ["ab", "cd", "ef"]
