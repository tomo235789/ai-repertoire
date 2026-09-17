# カード object-invert の Contract を検証するテスト
import pytest


def invert(d: dict) -> dict:
    return {v: k for k, v in d.items()}


def test_swaps_keys_and_values():
    """キーと値を入れ替える。型はそのまま（文字列化しない）"""
    code_to_name = {1: "red", 2: "blue"}
    result = invert(code_to_name)
    assert result == {"red": 1, "blue": 2}
    assert result["red"] is not None and isinstance(result["red"], int)


def test_does_not_mutate_input():
    """入力辞書を変更しない。返り値は新しい dict"""
    d = {1: "red"}
    result = invert(d)
    assert d == {1: "red"}
    assert result is not d


def test_preserves_insertion_order():
    """順序は元の辞書の挿入順"""
    assert list(invert({"x": 3, "y": 1})) == [3, 1]


def test_duplicate_values_keep_last_key_at_first_position():
    """値が重複したら最後のキーが残り、位置は最初に出現した場所"""
    assert invert({"b": 1, "a": 1}) == {1: "a"}
    result = invert({"a": 1, "b": 2, "c": 1})
    assert result == {1: "c", 2: "b"}
    assert list(result) == [1, 2]


def test_empty_dict_returns_empty_dict():
    """空の辞書を渡すと {} を返す"""
    assert invert({}) == {}


def test_unhashable_value_raises_and_none_is_allowed():
    """ハッシュ化できない値は TypeError。None はキーにできる"""
    with pytest.raises(TypeError):
        invert({"a": [1]})
    assert invert({"a": None}) == {None: "a"}


def test_equal_keys_collapse():
    """Pitfalls: 1 と True は同じキーとして扱われる"""
    assert invert({"a": 1, "b": True}) == {1: "b"}
