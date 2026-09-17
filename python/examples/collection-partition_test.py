"""カード collection-partition の Contract を検証するテスト"""

from itertools import count
from types import GeneratorType

import pytest
from more_itertools import partition


def test_returns_false_items_first_then_true_items_in_order():
    """返り値は (偽, 真) の順のジェネレータの組で、どちらも順序を保つ"""
    result = partition(lambda x: x % 2 == 0, [1, 2, 3, 4, 5])
    assert isinstance(result, tuple)
    falsy, truthy = result
    assert isinstance(falsy, GeneratorType)
    assert isinstance(truthy, GeneratorType)
    assert list(falsy) == [1, 3, 5]
    assert list(truthy) == [2, 4]


def test_does_not_mutate_input_and_keeps_references():
    """入力を変更せず、要素は同じ参照を返す"""
    a = {"ok": True}
    src = [a, {"ok": False}]
    falsy, truthy = partition(lambda o: o["ok"], src)
    assert list(truthy)[0] is a
    assert src == [{"ok": True}, {"ok": False}]


def test_is_lazy_and_queues_other_side():
    """取り出した分だけ入力を読み、相手側はキューに溜まる。各ジェネレータは 1 回だけ"""
    falsy, truthy = partition(lambda x: x % 2 == 0, count())
    assert next(truthy) == 0
    assert next(falsy) == 1

    seen = []

    def pred(x):
        seen.append(x)
        return x > 1

    falsy, truthy = partition(pred, [1, 2, 3, 4])
    assert seen == []
    assert next(truthy) == 2
    assert seen == [1, 2]
    assert next(falsy) == 1
    assert seen == [1, 2]
    assert list(truthy) == [3, 4]
    assert list(truthy) == []


def test_pred_is_called_once_per_element_in_order():
    """片方を読み切ると全要素に pred が 1 回ずつ順に呼ばれ、入力全体が消費される"""
    seen = []

    def pred(x):
        seen.append(x)
        return x > 1

    src = iter([1, 2, 3])
    falsy, truthy = partition(pred, src)
    assert list(falsy) == [1]
    assert seen == [1, 2, 3]
    assert list(src) == []
    assert list(truthy) == [2, 3]
    assert seen == [1, 2, 3]


def test_uses_truthiness_and_none_pred_means_bool():
    """戻り値は truthy / falsy で判定し、pred=None は bool"""
    falsy, truthy = partition(lambda x: x, [0, 1, "", 2, None])
    assert list(falsy) == [0, "", None]
    assert list(truthy) == [1, 2]
    falsy, truthy = partition(None, [0, 1, "", " "])
    assert list(falsy) == [0, ""]
    assert list(truthy) == [1, " "]


def test_empty_input_yields_two_empty_generators():
    """空のイテラブルは両方とも空"""
    falsy, truthy = partition(lambda x: x, [])
    assert list(falsy) == []
    assert list(truthy) == []


def test_pred_exception_propagates():
    """pred が投げた例外はそのまま伝わる"""

    def pred(x):
        raise RuntimeError("boom")

    falsy, _ = partition(pred, [1])
    with pytest.raises(RuntimeError):
        next(falsy)
