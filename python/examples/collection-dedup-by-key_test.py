"""カード collection-dedup-by-key の Contract を検証するテスト"""

from itertools import count

import pytest
from more_itertools import unique_everseen


def test_keeps_first_occurrence_in_order():
    """同じキーは最初の要素を残し、順序を保つ"""
    users = [{"id": 1, "name": "a"}, {"id": 2, "name": "b"}, {"id": 1, "name": "c"}]
    assert list(unique_everseen(users, key=lambda u: u["id"])) == [
        {"id": 1, "name": "a"},
        {"id": 2, "name": "b"},
    ]


def test_does_not_mutate_input_and_keeps_references():
    """入力を変更せず、要素は同じ参照を返す"""
    a = {"id": 1}
    src = [a, {"id": 1}]
    result = list(unique_everseen(src, key=lambda u: u["id"]))
    assert len(src) == 2
    assert result[0] is a


def test_is_lazy_generator_and_single_pass():
    """取り出した分だけ入力を読み、2 回目の走査は空になる"""
    assert next(unique_everseen(count())) == 0

    once = unique_everseen([1, 1, 2])
    assert list(once) == [1, 2]
    assert list(once) == []


def test_key_is_called_once_per_element_in_order():
    """key は各要素につき 1 回、先頭から順に呼ばれる"""
    seen = []

    def key(n):
        seen.append(n)
        return n

    list(unique_everseen([10, 20, 10], key=key))
    assert seen == [10, 20, 10]


def test_key_defaults_to_element_itself():
    """key を省略すると要素そのものがキーになる"""
    assert list(unique_everseen("AAaB", key=None)) == ["A", "a", "B"]
    assert list(unique_everseen("AAaB", key=str.lower)) == ["A", "B"]


def test_key_comparison_uses_hash_and_equality():
    """キーの比較は set と同じ（1 == 1.0 == True、nan は同一オブジェクトのみ等しい）"""
    assert list(unique_everseen([1, 1.0, True])) == [1]
    nan = float("nan")
    assert len(list(unique_everseen([nan, nan]))) == 1
    assert len(list(unique_everseen([float("nan"), float("nan")]))) == 2


def test_empty_input_yields_nothing():
    """空のイテラブルは何も返さない"""
    assert list(unique_everseen([], key=lambda x: x)) == []


def test_unhashable_key_raises_type_error():
    """ハッシュ不可なキーは TypeError（要素に達した時点で投げる）"""
    with pytest.raises(TypeError):
        list(unique_everseen([[1], [2], [1]]))
    with pytest.raises(TypeError):
        list(unique_everseen([{"a": 1}], key=lambda d: d))
    assert list(unique_everseen([[1], [2], [1]], key=tuple)) == [[1], [2]]
