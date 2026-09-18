"""カード map-key-by の Contract を検証するテスト"""

import pytest


def key_by(iterable, key):
    return {key(x): x for x in iterable}


def test_builds_lookup_dict_with_references():
    """キーから要素を引ける dict を作り、値は同じ参照"""
    users = [{"id": "u1", "name": "A"}, {"id": "u2", "name": "B"}]
    by_id = key_by(users, lambda u: u["id"])
    assert by_id["u2"]["name"] == "B"
    assert by_id["u1"] is users[0]
    assert type(by_id) is dict


def test_duplicate_keys_keep_last_element_at_first_position():
    """重複キーは最後の要素が残り、位置は最初に出現した場所"""
    dup = [{"id": "x", "v": 1}, {"id": "y", "v": 9}, {"id": "x", "v": 2}]
    result = key_by(dup, lambda d: d["id"])
    assert result == {"x": {"id": "x", "v": 2}, "y": {"id": "y", "v": 9}}
    assert list(result) == ["x", "y"]


def test_is_eager_and_key_is_evaluated_once_per_element_in_order():
    """キー式は各要素につき 1 回、先頭から順に評価される"""
    calls = []

    def key(x):
        calls.append(x)
        return x

    key_by([1, 2, 1], key)
    assert calls == [1, 2, 1]


def test_does_not_mutate_input():
    """入力を変更しない"""
    src = [{"id": "a"}]
    key_by(src, lambda d: d["id"])
    assert src == [{"id": "a"}]


def test_key_type_is_preserved_and_identity_uses_equality():
    """キーの型はそのまま。1 と 1.0 と True は同じキー、1 と '1' は別キー"""
    assert key_by([1, "1"], lambda x: x) == {1: 1, "1": "1"}
    assert key_by([1, 1.0, True], lambda x: x) == {1: True}
    assert list(key_by([1, 1.0, True], lambda x: x)) == [1]


def test_empty_input_returns_empty_dict():
    """空のイテラブルなら {}"""
    assert key_by([], lambda x: x) == {}


def test_unhashable_key_raises_type_error():
    """ハッシュ不可なキーは TypeError"""
    with pytest.raises(TypeError):
        key_by([[1]], lambda x: x)


def test_missing_key_raises_key_error_and_get_returns_default():
    """存在しないキーは KeyError。get で既定値を受けられる"""
    by_id = key_by([{"id": "a"}], lambda d: d["id"])
    with pytest.raises(KeyError):
        by_id["zz"]
    assert by_id.get("zz") is None


def test_keep_first_alternatives():
    """Alternatives: setdefault で最初を残す。reversed でも最初が残るが順序は変わる"""
    dup = [{"id": "x", "v": 1}, {"id": "y", "v": 9}, {"id": "x", "v": 2}]
    first = {}
    for d in dup:
        first.setdefault(d["id"], d)
    assert first == {"x": {"id": "x", "v": 1}, "y": {"id": "y", "v": 9}}
    assert list(first) == ["x", "y"]
    later = [{"id": "y"}, {"id": "x", "v": 1}, {"id": "x", "v": 2}]
    via_reversed = key_by(reversed(later), lambda d: d["id"])
    assert via_reversed == {"y": {"id": "y"}, "x": {"id": "x", "v": 1}}
    assert list(via_reversed) == ["x", "y"]
