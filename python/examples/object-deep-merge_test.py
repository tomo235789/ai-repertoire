# カード object-deep-merge の Contract を検証するテスト
import pytest
from mergedeep import Strategy, merge


def test_merges_nested_dicts_recursively():
    """ネストした辞書を再帰的にマージする"""
    defaults = {"retry": 3, "log": {"level": "info", "file": "app.log"}}
    overrides = {"log": {"level": "debug"}}
    assert merge({}, defaults, overrides) == {"retry": 3, "log": {"level": "debug", "file": "app.log"}}


def test_mutates_and_returns_destination():
    """第 1 引数を破壊的に更新し、それ自身を返す。sources は変更しない"""
    dest = {"x": {"y": 1}}
    src = {"x": {"z": 2}}
    result = merge(dest, src)
    assert result is dest
    assert dest == {"x": {"y": 1, "z": 2}}
    assert src == {"x": {"z": 2}}


def test_empty_destination_keeps_sources_unchanged():
    """merge({}, a, b) の形なら a も b も変わらない"""
    a = {"log": {"level": "info"}, "tags": [1, 2, 3]}
    b = {"log": {"level": "debug"}, "tags": [9]}
    merge({}, a, b)
    assert a == {"log": {"level": "info"}, "tags": [1, 2, 3]}
    assert b == {"log": {"level": "debug"}, "tags": [9]}


def test_later_sources_win():
    """sources は左から順に適用され、後のものが勝つ"""
    assert merge({}, {"a": 1}, {"a": 2}, {"a": 3}) == {"a": 3}


def test_replace_strategy_replaces_non_mapping_values():
    """既定の REPLACE ではリストやスカラーは後の値で丸ごと置き換える（連結しない）"""
    assert merge({}, {"tags": [1, 2, 3]}, {"tags": [9]}) == {"tags": [9]}
    assert merge({}, {"a": {"b": 1}}, {"a": 5}) == {"a": 5}
    assert merge({}, {"a": 5}, {"a": {"b": 1}}) == {"a": {"b": 1}}


def test_values_are_deep_copied_from_sources():
    """sources の値は deepcopy され、返り値と参照を共有しない"""
    src = {"a": {"b": {"c": 1}}, "tags": [1]}
    result = merge({}, src)
    assert result == src
    assert result["a"] is not src["a"]
    assert result["a"]["b"] is not src["a"]["b"]
    assert result["tags"] is not src["tags"]


def test_none_overrides_existing_value():
    """sources の値が None でも上書きする"""
    assert merge({}, {"a": 1}, {"a": None}) == {"a": None}


def test_key_order_is_destination_then_new_keys():
    """キー順は destination の順の後に、新たに現れたキーがその順で並ぶ"""
    result = merge({}, {"b": 1, "a": 2}, {"c": 3, "a": 4})
    assert list(result) == ["b", "a", "c"]


def test_additive_strategy_concatenates_collections():
    """ADDITIVE では list / tuple / set を連結し、スカラーは置き換える"""
    assert merge({}, {"t": [1, 2]}, {"t": [3]}, strategy=Strategy.ADDITIVE) == {"t": [1, 2, 3]}
    assert merge({}, {"t": (1,)}, {"t": (2,)}, strategy=Strategy.ADDITIVE) == {"t": (1, 2)}
    assert merge({}, {"t": {1}}, {"t": {2}}, strategy=Strategy.ADDITIVE) == {"t": {1, 2}}
    assert merge({}, {"t": 1}, {"t": 2}, strategy=Strategy.ADDITIVE) == {"t": 2}


def test_typesafe_strategies_raise_on_type_mismatch():
    """TYPESAFE_REPLACE / TYPESAFE_ADDITIVE / TYPESAFE は型が異なると TypeError。REPLACE は投げない"""
    for strategy in (Strategy.TYPESAFE_REPLACE, Strategy.TYPESAFE_ADDITIVE, Strategy.TYPESAFE):
        with pytest.raises(TypeError):
            merge({}, {"t": 1}, {"t": "s"}, strategy=strategy)
    assert merge({}, {"t": 1}, {"t": 2}, strategy=Strategy.TYPESAFE_REPLACE) == {"t": 2}
    assert merge({}, {"t": 1}, {"t": "s"}) == {"t": "s"}


def test_no_sources_returns_destination_as_is():
    """sources が無ければ destination をそのまま返す"""
    assert merge({}) == {}


def test_shallow_merge_alternatives_replace_nested_dicts():
    """Alternatives: {**a, **b} と a | b はネストした辞書を丸ごと置き換える"""
    a = {"log": {"level": "info", "file": "app.log"}}
    b = {"log": {"level": "debug"}}
    assert {**a, **b} == {"log": {"level": "debug"}}
    assert a | b == {"log": {"level": "debug"}}
