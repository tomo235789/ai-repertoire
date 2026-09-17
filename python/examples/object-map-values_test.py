# カード object-map-values の Contract を検証するテスト
import pytest


def map_values(d: dict, f) -> dict:
    return {k: f(v) for k, v in d.items()}


def test_transforms_each_value_keeping_keys():
    """キーはそのままに各値を変換する"""
    scores = {"alice": [80, 90], "bob": [70]}
    assert map_values(scores, len) == {"alice": 2, "bob": 1}


def test_preserves_key_order():
    """キーの順序を保持する"""
    d = {"c": 1, "a": 2, "b": 3}
    assert list(map_values(d, lambda v: v * 10)) == ["c", "a", "b"]


def test_does_not_mutate_input_and_keeps_identity_of_returned_values():
    """入力辞書を変更せず、f が返した値がそのまま入る（入力の値を返せば同じ参照）"""
    inner = [1, 2]
    d = {"a": inner}
    result = map_values(d, lambda v: v)
    assert d == {"a": inner}
    assert result is not d
    assert result["a"] is inner


def test_callback_called_once_per_key_in_order():
    """f は各キーにつきちょうど 1 回、挿入順に呼ばれる"""
    calls = []

    def f(v):
        calls.append(v)
        return v

    map_values({"x": 1, "y": 2, "z": 3}, f)
    assert calls == [1, 2, 3]


def test_empty_dict_returns_empty_dict():
    """空の辞書を渡すと {} を返す"""
    assert map_values({}, len) == {}


def test_callback_exception_propagates():
    """f が投げた例外はそのまま伝播する"""

    def boom(_):
        raise ValueError("boom")

    with pytest.raises(ValueError, match="boom"):
        map_values({"a": 1}, boom)


def test_mutating_input_during_iteration_raises():
    """Pitfalls: 走査中に入力辞書を変更すると RuntimeError"""
    d = {"a": 1}

    def f(v):
        d["b"] = 2
        return v

    with pytest.raises(RuntimeError):
        map_values(d, f)
