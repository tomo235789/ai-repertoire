"""function-once: 引数無しの関数に付けた functools.cache の Contract を検証する。"""

import asyncio
import threading
from concurrent.futures import ThreadPoolExecutor
from functools import cache

import pytest


def test_runs_only_once_and_returns_same_object() -> None:
    """1 回目だけ関数を実行し、2 回目以降は 1 回目の戻り値（同じオブジェクト）を返す。"""
    calls: list[int] = []

    @cache
    def init() -> dict[str, int]:
        calls.append(1)
        return {"n": len(calls)}

    first = init()
    second = init()
    assert first == {"n": 1}
    assert first is second
    assert calls == [1]


def test_exception_is_retried_on_next_call() -> None:
    """例外を投げた場合は実行済みにならず、次の呼び出しで再実行される。"""
    calls: list[int] = []

    @cache
    def init() -> int:
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("first")
        return len(calls)

    with pytest.raises(RuntimeError, match="first"):
        init()
    assert init() == 2
    assert init() == 2
    assert calls == [1, 1]


def test_cache_clear_resets_to_unexecuted() -> None:
    """cache_clear を呼ぶと未実行に戻り、次の呼び出しで再実行される。"""
    calls: list[int] = []

    @cache
    def init() -> int:
        calls.append(1)
        return len(calls)

    assert init() == 1
    init.cache_clear()
    assert init() == 2
    assert calls == [1, 1]


def test_concurrent_first_calls_may_run_more_than_once() -> None:
    """保存前に別スレッドから呼ばれると関数が複数回実行される（排他は保証されない）。"""
    calls: list[int] = []
    # 3 スレッドすべてが関数本体に入ってから戻る（決定的に 3 回実行させる）
    barrier = threading.Barrier(3, timeout=1)

    @cache
    def init() -> int:
        calls.append(1)
        barrier.wait()
        return 1

    # Future.result() で各スレッドの例外（Barrier のタイムアウトなど）をテストへ伝播させる
    with ThreadPoolExecutor(max_workers=3) as pool:
        results = [fut.result() for fut in [pool.submit(init) for _ in range(3)]]
    assert results == [1, 1, 1]
    assert len(calls) == 3


def test_original_function_is_unchanged() -> None:
    """状態は装飾された関数が持ち、__wrapped__ の元関数は毎回実行される。"""
    calls: list[int] = []

    @cache
    def init() -> int:
        calls.append(1)
        return len(calls)

    assert init() == 1
    assert init.__wrapped__() == 2
    assert init.__wrapped__() == 3
    assert init() == 1


def test_arguments_make_separate_once_states() -> None:
    """Pitfalls: 引数を渡すと引数ごとに別々に 1 回ずつ実行される。"""
    calls: list[str] = []

    @cache
    def init(name: str) -> str:
        calls.append(name)
        return name.upper()

    assert init("a") == "A"
    assert init("b") == "B"
    assert init("a") == "A"
    assert calls == ["a", "b"]


def test_async_function_shares_coroutine_object() -> None:
    """Alternatives: async def に付けるとコルーチンが共有され、2 回目の await で RuntimeError になる。"""

    @cache
    async def init() -> int:
        return 1

    async def main() -> None:
        assert await init() == 1
        with pytest.raises(RuntimeError, match="cannot reuse already awaited coroutine"):
            await init()

    asyncio.run(main())
