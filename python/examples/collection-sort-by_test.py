"""カード collection-sort-by の Contract を検証するテスト"""

import pytest


def test_is_stable_even_with_reverse():
    """キーが等しい要素は元の相対順を保つ（reverse=True でも）"""
    items = [("a", 1), ("b", 1), ("c", 0)]
    assert sorted(items, key=lambda t: t[1]) == [("c", 0), ("a", 1), ("b", 1)]
    assert sorted(items, key=lambda t: t[1], reverse=True) == [("a", 1), ("b", 1), ("c", 0)]


def test_does_not_mutate_input_and_keeps_references():
    """入力を変更せず、新しいリストの要素は同じ参照。イテレータも受け取る"""
    a = {"k": 2}
    src = [a, {"k": 1}]
    result = sorted(src, key=lambda o: o["k"])
    assert src == [{"k": 2}, {"k": 1}]
    assert result is not src
    assert result[1] is a
    assert sorted(iter([3, 1, 2])) == [1, 2, 3]


def test_is_eager():
    """返る時点で入力をすべて読み終えている"""
    seen = []

    def gen():
        for i in (3, 1, 2):
            seen.append(i)
            yield i

    sorted(gen())
    assert seen == [3, 1, 2]


def test_key_is_called_once_per_element_in_order():
    """key は各要素につき 1 回、先頭から順に呼ばれる"""
    seen = []

    def key(n):
        seen.append(n)
        return n

    sorted([3, 1, 2], key=key)
    assert seen == [3, 1, 2]


def test_multiple_keys_compare_left_to_right():
    """タプルのキーは左から順に比較し、前が等しいときだけ次で比較する"""
    users = [{"name": "b", "age": 30}, {"name": "a", "age": 30}, {"name": "c", "age": 20}]
    assert sorted(users, key=lambda u: (u["age"], u["name"])) == [
        {"name": "c", "age": 20},
        {"name": "a", "age": 30},
        {"name": "b", "age": 30},
    ]


def test_reverse_flips_all_keys():
    """reverse=True は全キーをまとめて降順にする"""
    items = [("b", 2), ("a", 2), ("c", 1)]
    assert sorted(items, key=lambda t: (t[1], t[0]), reverse=True) == [("b", 2), ("a", 2), ("c", 1)]


def test_empty_input_returns_empty_list():
    """空のイテラブルは [] を返す"""
    assert sorted([]) == []


def test_incomparable_keys_raise_type_error():
    """None や文字列と数値の混在は TypeError。タプルで先に振り分ければ末尾に置ける"""
    with pytest.raises(TypeError):
        sorted([1, None, 2])
    with pytest.raises(TypeError):
        sorted([1, "a"])
    assert sorted([2, None, 1, None], key=lambda x: (x is None, x)) == [1, 2, None, None]
