"""カード collection-sliding-window の Contract を検証するテスト"""

from itertools import count

import pytest
from more_itertools import sliding_window, windowed


def test_windows_keep_order_and_advance_by_step():
    """窓は先頭から step 刻みで並び、窓の中も元の並び順"""
    assert list(windowed([1, 2, 3, 4, 5], 3)) == [(1, 2, 3), (2, 3, 4), (3, 4, 5)]
    assert list(windowed([1, 2, 3, 4, 5], 3, step=2)) == [(1, 2, 3), (3, 4, 5)]


def test_does_not_mutate_input_and_keeps_references():
    """入力を変更せず、各窓は新しいタプルで要素は同じ参照"""
    a = {"k": 1}
    src = [a, {"k": 2}]
    result = list(windowed(src, 2))
    assert src == [{"k": 1}, {"k": 2}]
    assert isinstance(result[0], tuple)
    assert result[0][0] is a


def test_is_lazy_and_single_pass():
    """窓 1 つ分ずつ入力を読み、2 回目の走査は空になる"""
    assert next(windowed(count(), 3)) == (0, 1, 2)
    once = windowed([1, 2, 3], 2)
    assert list(once) == [(1, 2), (2, 3)]
    assert list(once) == []


def test_step_larger_than_n_skips_elements():
    """step > n なら窓の間の要素は飛ばされる"""
    assert list(windowed([1, 2, 3, 4, 5, 6], 2, step=3)) == [(1, 2), (4, 5)]


def test_tail_is_filled_not_dropped():
    """はみ出す末尾は fillvalue で埋める。前の窓に含まれた要素しか残らなければ出力しない"""
    assert list(windowed([1, 2, 3, 4, 5, 6, 7], 3, step=3)) == [(1, 2, 3), (4, 5, 6), (7, None, None)]
    assert list(windowed([1, 2, 3, 4, 5, 6], 3, step=2)) == [(1, 2, 3), (3, 4, 5), (5, 6, None)]
    assert list(windowed([1, 2, 3, 4, 5], 3, step=2)) == [(1, 2, 3), (3, 4, 5)]
    assert list(windowed([1, 2, 3, 4, 5], 2, step=4)) == [(1, 2), (5, None)]


def test_short_input_yields_single_filled_window():
    """入力長が n 未満なら fillvalue で埋めた窓を 1 つだけ返す"""
    assert list(windowed([1, 2], 3)) == [(1, 2, None)]
    assert list(windowed([1, 2], 3, fillvalue=0)) == [(1, 2, 0)]


def test_empty_input_yields_nothing():
    """空のイテラブルは何も返さない"""
    assert list(windowed([], 3)) == []


def test_invalid_n_or_step_raises_value_error():
    """n が 1 未満、または step が 1 未満なら ValueError"""
    with pytest.raises(ValueError):
        list(windowed([1, 2], 0))
    with pytest.raises(ValueError):
        list(windowed([1, 2], -1))
    with pytest.raises(ValueError):
        list(windowed([1, 2], 2, step=0))


def test_sliding_window_drops_incomplete_windows():
    """Alternatives: sliding_window は n 個そろった窓だけを返す"""
    assert list(sliding_window([1, 2, 3, 4], 2)) == [(1, 2), (2, 3), (3, 4)]
    assert list(sliding_window([1, 2], 3)) == []
