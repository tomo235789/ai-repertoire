"""function-memoize: functools.cache の Contract を検証する。"""

import gc
import threading
from concurrent.futures import ThreadPoolExecutor
import weakref
from functools import cache, lru_cache

import pytest


def test_returns_cached_value_for_same_arguments() -> None:
    """同じ引数なら 2 回目以降は関数を呼ばず、保存した戻り値をそのまま返す。"""
    calls: list[int] = []

    @cache
    def double(n: int) -> list[int]:
        calls.append(n)
        return [n * 2]

    first = double(3)
    second = double(3)
    assert first == [6]
    assert first is second
    assert calls == [3]


def test_all_arguments_form_the_key() -> None:
    """位置引数とキーワード引数のすべてがキーになり、第 2 引数を変えると再計算される。"""
    calls: list[tuple[int, int]] = []

    @cache
    def add(a: int, b: int = 1) -> int:
        calls.append((a, b))
        return a + b

    assert add(1, 2) == 3
    assert add(1, 3) == 4
    assert calls == [(1, 2), (1, 3)]


def test_positional_and_keyword_calls_are_different_keys() -> None:
    """位置で渡すかキーワードで渡すか、キーワードの順序が違うと別キーになる。"""
    calls: list[str] = []

    @cache
    def add(a: int, b: int) -> int:
        calls.append("call")
        return a + b

    assert add(1, 2) == add(1, b=2) == add(b=2, a=1) == add(a=1, b=2) == 3
    # 仕様上は「別エントリになり得る」だけなので、CPython の挙動（4 misses）を必須にしない
    info = add.cache_info()
    assert info.hits + info.misses == 4
    assert len(calls) == info.misses >= 1


def test_unhashable_argument_raises_type_error() -> None:
    """list を渡すと TypeError（unhashable type）になる。"""

    @cache
    def total(xs: list[int]) -> int:
        return sum(xs)

    with pytest.raises(TypeError, match="unhashable"):
        total([1, 2, 3])


def test_exception_is_not_cached() -> None:
    """関数が例外を投げた場合は保存されず、次回また呼ばれる。"""
    calls: list[int] = []

    @cache
    def fail(n: int) -> int:
        calls.append(n)
        raise ValueError("boom")

    for _ in range(2):
        with pytest.raises(ValueError, match="boom"):
            fail(1)
    assert calls == [1, 1]
    assert fail.cache_info().currsize == 0


def test_cache_info_and_cache_clear() -> None:
    """cache_info で hits / misses / currsize を確認でき、cache_clear で全消去できる。"""

    @cache
    def square(n: int) -> int:
        return n * n

    square(2)
    square(2)
    square(3)
    info = square.cache_info()
    assert (info.hits, info.misses, info.currsize, info.maxsize) == (1, 2, 2, None)

    square.cache_clear()
    info = square.cache_info()
    assert (info.hits, info.misses, info.currsize) == (0, 0, 0)


def test_concurrent_calls_may_run_function_more_than_once() -> None:
    """保存前に別スレッドから呼ばれると関数が複数回実行される（キャッシュは壊れない）。"""
    calls: list[int] = []
    # 3 スレッドすべてが関数本体に入ってから戻る（決定的に 3 回実行させる）
    barrier = threading.Barrier(3, timeout=1)

    @cache
    def slow() -> int:
        calls.append(1)
        barrier.wait()
        return 1

    # Future.result() で各スレッドの例外（Barrier のタイムアウトなど）をテストへ伝播させる
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = [fut.result() for fut in [pool.submit(slow) for _ in range(3)]]
    assert results == [1, 1, 1]
    assert len(calls) == 3
    assert slow() == 1
    assert slow.cache_info().currsize == 1


def test_lru_cache_alternative_evicts_oldest_entry() -> None:
    """Alternatives: lru_cache(maxsize) は上限を超えると古いエントリを追い出す。"""

    @lru_cache(maxsize=2)
    def square(n: int) -> int:
        return n * n

    square(1)
    square(2)
    square(3)
    assert square.cache_info().currsize == 2
    square(1)
    assert square.cache_info().misses == 4


def test_method_cache_keeps_instance_alive() -> None:
    """Pitfalls: メソッドに付けると self がキャッシュに保持され、インスタンスが解放されない。"""

    class Holder:
        @cache
        def value(self, n: int) -> int:
            return n

    holder = Holder()
    holder.value(1)
    ref = weakref.ref(holder)
    del holder
    gc.collect()
    assert ref() is not None
    Holder.value.cache_clear()
    gc.collect()
    assert ref() is None
