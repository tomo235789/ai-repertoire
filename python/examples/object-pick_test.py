# カード object-pick の Contract を検証するテスト
import operator

import pytest


def pick(d: dict, keys) -> dict:
    return {k: d[k] for k in keys if k in d}


def test_picks_only_given_keys():
    """指定したキーだけを持つ辞書を返す"""
    user = {"id": 1, "name": "a", "password": "x"}
    assert pick(user, ["id", "name"]) == {"id": 1, "name": "a"}


def test_does_not_mutate_input_and_returns_shallow_copy():
    """入力辞書を変更せず、値は浅いコピー（ネストした辞書は同じ参照）"""
    nested = {"z": 1}
    user = {"id": 1, "nested": nested}
    result = pick(user, ["nested"])
    assert user == {"id": 1, "nested": nested}
    assert result is not user
    assert result["nested"] is nested


def test_missing_keys_are_ignored_and_none_values_are_kept():
    """存在しないキーは無視され、値が None のキーは None のまま含まれる"""
    d = {"a": None, "b": 2}
    assert pick(d, ["a", "missing"]) == {"a": None}
    assert "missing" not in pick(d, ["missing"])


def test_result_follows_keys_order_and_dedupes():
    """返り値のキーは keys の順で、重複したキーは 1 つにまとまる"""
    d = {"a": 1, "b": 2, "c": 3}
    result = pick(d, ["c", "a", "c"])
    assert list(result) == ["c", "a"]
    assert result == {"c": 3, "a": 1}


def test_empty_keys_returns_empty_dict():
    """keys が空なら {} を返す"""
    assert pick({"a": 1}, []) == {}


def test_unhashable_key_raises_type_error():
    """ハッシュ化できないキーがあると TypeError を投げる"""
    with pytest.raises(TypeError):
        pick({"a": 1}, [["a"]])


def test_itemgetter_raises_key_error_for_missing_key():
    """Alternatives: operator.itemgetter は存在しないキーで KeyError になる"""
    d = {"id": 1, "name": "a"}
    assert operator.itemgetter("id", "name")(d) == (1, "a")
    with pytest.raises(KeyError):
        operator.itemgetter("id", "missing")(d)


def test_get_variant_includes_missing_keys_as_none():
    """Pitfalls: d.get(k) で書くと存在しないキーが None で含まれる"""
    d = {"a": 1}
    assert {k: d.get(k) for k in ["a", "missing"]} == {"a": 1, "missing": None}
