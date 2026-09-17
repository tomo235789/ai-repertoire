"""async-sleep: asyncio.sleep の Contract を検証する。"""

import asyncio
import time

import pytest


def test_waits_for_delay_and_returns_result() -> None:
    """delay 秒後に result を返し、省略時は None を返す。"""

    async def main() -> None:
        start = time.perf_counter()
        assert await asyncio.sleep(0.01, result="done") == "done"
        assert time.perf_counter() - start >= 0.01
        assert await asyncio.sleep(0.001) is None

    asyncio.run(main())


def test_other_tasks_run_while_sleeping() -> None:
    """待っている間はイベントループを止めず、ほかのタスクが実行される。"""
    order: list[str] = []

    async def slow() -> None:
        order.append("slow:start")
        await asyncio.sleep(0.01)
        order.append("slow:end")

    async def quick() -> None:
        order.append("quick")

    async def main() -> None:
        await asyncio.gather(slow(), quick())

    asyncio.run(main())
    assert order == ["slow:start", "quick", "slow:end"]


def test_zero_or_negative_delay_yields_once_without_waiting() -> None:
    """0 以下の delay は実時間の待機をせず、制御を 1 回譲ってすぐ戻る。負数でも例外にならない。"""
    order: list[str] = []

    async def yielder() -> None:
        order.append("y:start")
        await asyncio.sleep(-1)
        order.append("y:end")

    async def other() -> None:
        order.append("other")

    async def main() -> None:
        assert await asyncio.sleep(-1) is None
        assert await asyncio.sleep(0) is None
        await asyncio.gather(yielder(), other())

    asyncio.run(main())
    assert order == ["y:start", "other", "y:end"]


def test_cancel_raises_cancelled_error() -> None:
    """待機中にキャンセルされると CancelledError になり、result は返らない。"""

    async def main() -> None:
        task = asyncio.create_task(asyncio.sleep(10, result="never"))
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert task.cancelled()

    asyncio.run(main())


def test_non_numeric_delay_raises_type_error() -> None:
    """delay に文字列や None を渡すと TypeError になる。"""

    async def main() -> None:
        with pytest.raises(TypeError):
            await asyncio.sleep("1")
        with pytest.raises(TypeError):
            await asyncio.sleep(None)

    asyncio.run(main())
