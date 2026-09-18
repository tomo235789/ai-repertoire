"""カード map-count-by の Contract を検証するテスト"""

from collections import Counter

import pytest


def test_counts_by_key_function_in_first_seen_order():
    """キー関数の結果ごとに数え、キーは初出順"""
    counts = Counter(len(w) for w in ["apple", "bob", "cat", "dove"])
    assert counts == {5: 1, 3: 2, 4: 1}
    assert list(counts) == [5, 3, 4]
    assert isinstance(counts, Counter)
    assert isinstance(counts, dict)


def test_is_eager_and_does_not_mutate_input():
    """入力を読み切り、入力は変わらない"""
    seen = []

    def gen():
        for i in [1, 1, 2]:
            seen.append(i)
            yield i

    Counter(gen())
    assert seen == [1, 1, 2]
    src = ["a", "b", "a"]
    Counter(src)
    assert src == ["a", "b", "a"]


def test_most_common_orders_by_count_then_first_seen():
    """most_common は回数の多い順、同数は初出順"""
    c = Counter(["c", "a", "b", "a", "c"])
    assert c.most_common() == [("c", 2), ("a", 2), ("b", 1)]
    assert c.most_common(1) == [("c", 2)]
    assert Counter().most_common() == []


def test_missing_key_is_zero_and_not_inserted():
    """無いキーは 0 を返し、KeyError にならず挿入もされない"""
    c = Counter("aab")
    assert c["z"] == 0
    assert "z" not in c
    assert len(c) == 2
    c["z"] += 1
    assert c["z"] == 1


def test_key_identity_uses_hash_and_equality():
    """1 と 1.0 と True は同じキー、1 と '1' は別キー。ハッシュ不可は TypeError"""
    assert Counter([1, 1.0, True, "1"]) == {1: 3, "1": 1}
    with pytest.raises(TypeError):
        Counter([[1]])


def test_empty_input_returns_empty_counter():
    """空のイテラブルなら空の Counter"""
    assert Counter([]) == Counter()
    assert len(Counter(iter([]))) == 0


def test_update_and_subtract_mutate_and_keep_non_positive_counts():
    """update は加算、subtract は減算で c を書き換え、0 や負も残す"""
    c = Counter("aab")
    c.update("ab")
    assert c == {"a": 3, "b": 2}
    c.subtract({"a": 3, "b": 5})
    assert c == {"a": 0, "b": -3}
    assert "a" in c


def test_operators_return_new_counter_and_drop_non_positive():
    """+ / - / & / | は新しい Counter を返し、0 以下のキーを落とす"""
    a = Counter("aab")
    b = Counter("abbb")
    assert a + b == {"a": 3, "b": 4}
    assert a - b == {"a": 1}
    assert a & b == {"a": 1, "b": 1}
    assert a | b == {"a": 2, "b": 3}
    assert a == {"a": 2, "b": 1}
    assert Counter({"x": 0, "y": 1}) + Counter() == {"y": 1}


def test_total_sums_counts():
    """total() は合計で sum(c.values()) と同じ"""
    c = Counter("abbccc")
    assert c.total() == 6
    assert c.total() == sum(c.values())
