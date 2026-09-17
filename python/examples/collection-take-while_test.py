"""カード collection-take-while の Contract を検証するテスト"""

from itertools import count, dropwhile, takewhile

import pytest
from more_itertools import before_and_after


def test_returns_prefix_in_order():
    """条件を満たす先頭部分を順序どおり返し、その後の真の要素は取り出さない"""
    assert list(takewhile(lambda x: x < 3, [1, 2, 3, 4, 1])) == [1, 2]


def test_does_not_mutate_input_and_keeps_references():
    """入力を変更せず、要素は同じ参照を返す"""
    a = {"k": 1}
    src = [a, {"k": 5}]
    result = list(takewhile(lambda o: o["k"] < 3, src))
    assert src == [{"k": 1}, {"k": 5}]
    assert result[0] is a


def test_is_lazy_and_single_pass():
    """取り出した分だけ入力を読み、2 回目の走査は空になる"""
    assert next(takewhile(lambda x: True, count())) == 0
    once = takewhile(lambda x: x < 3, [1, 2, 3])
    assert list(once) == [1, 2]
    assert list(once) == []


def test_predicate_is_called_up_to_first_false():
    """predicate は先頭から順に、最初に偽を返した要素まで呼ばれる"""
    seen = []

    def pred(x):
        seen.append(x)
        return x < 3

    assert list(takewhile(pred, [1, 2, 3, 4, 1])) == [1, 2]
    assert seen == [1, 2, 3]


def test_first_false_element_is_consumed_and_lost():
    """最初に偽になった要素は結果に含まれず、イテレータからも消費されている"""
    it = iter([1, 2, 3, 4, 1])
    assert list(takewhile(lambda x: x < 3, it)) == [1, 2]
    assert list(it) == [4, 1]


def test_uses_truthiness():
    """戻り値は truthy / falsy で判定する"""
    assert list(takewhile(lambda x: x, [1, "a", 0, 2])) == [1, "a"]


def test_all_true_or_first_false_or_empty():
    """すべて真なら全要素、先頭で偽なら空、空入力なら空"""
    assert list(takewhile(lambda x: x < 9, [1, 2])) == [1, 2]
    assert list(takewhile(lambda x: x < 0, [1, 2])) == []
    assert list(takewhile(lambda x: x < 3, [])) == []


def test_predicate_exception_propagates():
    """predicate が投げた例外はそのまま伝わる"""

    def pred(x):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        list(takewhile(pred, [1]))


def test_dropwhile_and_before_and_after_keep_the_rest():
    """Alternatives: dropwhile は残りを返し、before_and_after は打ち切った要素を失わない"""
    xs = [1, 2, 3, 4, 1]
    assert list(takewhile(lambda x: x < 3, xs)) + list(dropwhile(lambda x: x < 3, xs)) == xs
    head, rest = before_and_after(lambda x: x < 3, iter(xs))
    assert list(head) == [1, 2]
    assert list(rest) == [3, 4, 1]
