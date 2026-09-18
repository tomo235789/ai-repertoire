"""カード iter-to-array の Contract を検証するテスト"""

from itertools import islice

import pytest


def test_is_eager_and_keeps_order():
    """呼んだ時点でイテラブルを終端まで走査し、順序を保った新しい list を返す"""
    seen = []

    def gen():
        for i in range(3):
            seen.append(i)
            yield i

    result = list(gen())
    assert result == [0, 1, 2]
    assert seen == [0, 1, 2]
    assert isinstance(result, list)


def test_keeps_references():
    """要素は同じ参照のまま入る"""
    a = {"k": 1}
    assert list(iter([a]))[0] is a


def test_consumes_iterator_and_excludes_already_pulled_elements():
    """既に next() で進めた分は含まれず、list() の後はイテレータが空"""
    it = iter([1, 2, 3])
    next(it)
    assert list(it) == [2, 3]
    assert list(it) == []


def test_runs_generator_finally_and_discards_return_value():
    """ジェネレータの finally が走り、return した値はリストに含まれない"""
    closed = []

    def gen():
        try:
            yield 1
            yield 2
        finally:
            closed.append(True)
        return "ignored"

    assert list(gen()) == [1, 2]
    assert closed == [True]


def test_list_input_is_shallow_copied_and_other_iterables_work():
    """リストは浅いコピー。dict はキー、文字列は 1 文字ずつ"""
    src = [[1], [2]]
    copied = list(src)
    assert copied == src
    assert copied is not src
    assert copied[0] is src[0]
    assert list({"a": 1, "b": 2}) == ["a", "b"]
    assert list("ab") == ["a", "b"]


def test_empty_input_returns_empty_list():
    """空のイテラブルや引数なしなら []"""
    assert list(iter([])) == []
    assert list() == []


def test_non_iterable_raises_type_error():
    """イテラブルでないものを渡すと TypeError"""
    with pytest.raises(TypeError):
        list(1)


def test_tuple_and_sorted_and_islice_alternatives():
    """Alternatives: tuple / sorted で確定でき、無限イテレータは islice で区切る"""
    assert tuple(x * 10 for x in [1, 2]) == (10, 20)
    assert sorted(iter([3, 1, 2])) == [1, 2, 3]

    def naturals():
        n = 0
        while True:
            yield n
            n += 1

    assert list(islice(naturals(), 3)) == [0, 1, 2]
