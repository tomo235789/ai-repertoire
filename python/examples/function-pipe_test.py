"""function-pipe: toolz.pipe の Contract を検証する。"""

import asyncio
from collections.abc import Callable
from functools import partial

import pytest
from toolz import compose_left, pipe


def double(n: int) -> int:
    return n * 2


def to_label(n: int) -> str:
    return f"total: {n}"


def test_applies_functions_left_to_right() -> None:
    """data を最初の関数に渡し、以降は直前の戻り値を左から順に渡す。"""
    assert pipe(3, double, to_label) == "total: 6"
    assert pipe(3, to_label, str.upper) == "TOTAL: 3"


def test_executes_synchronously_in_order() -> None:
    """各関数は呼び出し時に同期的に順番どおり実行される。"""
    order: list[str] = []

    def step(name: str) -> Callable[[int], int]:
        def run(n: int) -> int:
            order.append(name)
            return n + 1

        return run

    assert pipe(0, step("a"), step("b"), step("c")) == 3
    assert order == ["a", "b", "c"]


def test_no_functions_returns_data_unchanged() -> None:
    """関数を 0 個で呼ぶと data をそのまま返す。"""
    data = [1, 2]
    assert pipe(data) is data


def test_function_with_two_required_arguments_raises() -> None:
    """各関数は引数 1 つで呼ばれるので、必須引数が 2 つの関数を渡すと TypeError になる。"""

    def add(a: int, b: int) -> int:
        return a + b

    with pytest.raises(TypeError):
        pipe(1, add)


def test_async_function_is_not_awaited() -> None:
    """非同期関数は await されず、コルーチンオブジェクトが次の関数に渡される。"""
    received: list[object] = []

    async def fetch(n: int) -> int:
        return n

    def capture(value: object) -> object:
        received.append(value)
        return value

    result = pipe(1, fetch, capture)
    assert asyncio.iscoroutine(result)
    assert received == [result]
    result.close()


def test_functions_are_not_modified() -> None:
    """渡した関数は変更されず、pipe の後も単独で同じように呼べる。"""
    before = double.__code__
    pipe(1, double, to_label)
    assert double.__code__ is before
    assert double(4) == 8


def test_compose_left_alternative_builds_a_function() -> None:
    """Alternatives: compose_left は値を渡さずに合成した関数を作り、pipe と同じ結果になる。"""
    summarize = compose_left(double, to_label)
    assert summarize(3) == pipe(3, double, to_label)
    assert compose_left()(5) == 5


def test_partial_for_multi_argument_step() -> None:
    """Alternatives: 複数引数の関数は partial で残り 1 引数にしてから渡す。"""
    assert pipe([1, 2, 3], partial(map, double), list) == [2, 4, 6]
