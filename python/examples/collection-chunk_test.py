"""カード collection-chunk の Contract を検証するテスト"""

from itertools import batched

import pytest
import sys


def test_keeps_order_and_last_batch_is_shorter():
    """順序を保ったまま n ごとに分割し、最後は短くなる"""
    assert list(batched([1, 2, 3, 4, 5], 2)) == [(1, 2), (3, 4), (5,)]


def test_does_not_mutate_input_and_keeps_references():
    """入力を変更せず、各バッチは要素の参照を共有する新しいタプル"""
    src = [{"k": 1}, {"k": 2}, {"k": 3}]
    result = list(batched(src, 2))
    assert src == [{"k": 1}, {"k": 2}, {"k": 3}]
    assert isinstance(result[0], tuple)
    assert result[0][0] is src[0]


def test_is_lazy_and_single_pass():
    """バッチ 1 つ分だけ入力を読み進め、2 回目の走査は空になる"""
    seen = []

    def gen():
        for i in range(5):
            seen.append(i)
            yield i

    it = batched(gen(), 2)
    assert next(it) == (0, 1)
    assert seen == [0, 1]

    once = batched([1, 2, 3], 2)
    assert list(once) == [(1, 2), (3,)]
    assert list(once) == []


@pytest.mark.skipif(sys.version_info < (3, 13), reason="strict 引数は Python 3.13 以降")
def test_strict_raises_on_incomplete_last_batch():
    """strict=True で最後のバッチが n 未満なら ValueError"""
    with pytest.raises(ValueError):
        list(batched([1, 2, 3], 2, strict=True))
    assert list(batched([1, 2, 3, 4], 2, strict=True)) == [(1, 2), (3, 4)]


def test_empty_input_yields_nothing():
    """空のイテラブルは何も返さない"""
    assert list(batched([], 3)) == []


def test_invalid_n_raises():
    """n が 1 未満なら ValueError、整数でなければ TypeError"""
    with pytest.raises(ValueError):
        list(batched([1, 2], 0))
    with pytest.raises(ValueError):
        list(batched([1, 2], -1))
    with pytest.raises(TypeError):
        list(batched([1, 2], 1.5))
