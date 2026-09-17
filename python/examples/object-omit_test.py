# カード object-omit の Contract を検証するテスト
import pytest


def omit(d: dict, excluded) -> dict:
    return {k: v for k, v in d.items() if k not in excluded}


def test_omits_given_keys():
    """指定したキーを除いた辞書を返す"""
    user = {"id": 1, "name": "a", "password": "x"}
    assert omit(user, {"password"}) == {"id": 1, "name": "a"}


def test_does_not_mutate_input_and_returns_shallow_copy():
    """入力辞書を変更せず、値は浅いコピー（ネストした辞書は同じ参照）"""
    nested = {"z": 1}
    user = {"id": 1, "password": "x", "nested": nested}
    result = omit(user, {"password"})
    assert user == {"id": 1, "password": "x", "nested": nested}
    assert result["nested"] is nested


def test_preserves_original_order():
    """残ったキーの順序は元の辞書のまま"""
    d = {"c": 3, "a": 1, "b": 2}
    assert list(omit(d, {"a"})) == ["c", "b"]


def test_missing_keys_are_ignored():
    """存在しないキーを excluded に入れても無視される"""
    d = {"a": 1}
    assert omit(d, {"missing"}) == {"a": 1}


def test_all_excluded_returns_empty_and_empty_excluded_returns_copy():
    """すべて除くと {}、excluded が空なら同じ内容の別オブジェクト"""
    d = {"a": 1, "b": 2}
    assert omit(d, {"a", "b"}) == {}
    result = omit(d, set())
    assert result == d
    assert result is not d


def test_list_excluded_gives_same_result_as_set():
    """excluded がリストでも set と同じ結果になる"""
    d = {"a": 1, "b": 2}
    assert omit(d, ["a"]) == omit(d, {"a"}) == {"b": 2}


def test_pop_and_del_mutate_original():
    """Alternatives / Pitfalls: pop と del は元の辞書を変える。del は存在しないと KeyError"""
    d = {"a": 1, "b": 2}
    assert d.pop("missing", None) is None
    del d["a"]
    assert d == {"b": 2}
    with pytest.raises(KeyError):
        del d["missing"]
