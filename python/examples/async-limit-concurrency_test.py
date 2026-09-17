"""async-limit-concurrency: asyncio.Semaphore の Contract を検証する。"""

import asyncio

import pytest


def test_limits_concurrent_tasks() -> None:
    """async with sem で同時実行数が value 以下に抑えられ、抜けるときに解放される。"""
    sem = asyncio.Semaphore(2)
    running = 0
    peak = 0

    async def work() -> None:
        nonlocal running, peak
        async with sem:
            running += 1
            peak = max(peak, running)
            await asyncio.sleep(0.01)
            running -= 1

    async def main() -> None:
        await asyncio.gather(*(work() for _ in range(6)))

    asyncio.run(main())
    assert peak == 2
    assert sem.locked() is False


def test_releases_even_when_block_raises() -> None:
    """ブロックの中で例外が出ても解放される。"""
    sem = asyncio.Semaphore(1)

    async def main() -> None:
        with pytest.raises(ValueError, match="inside"):
            async with sem:
                raise ValueError("inside")
        assert sem.locked() is False
        async with sem:
            assert sem.locked() is True

    asyncio.run(main())


def test_acquire_returns_immediately_when_available() -> None:
    """空きがあれば acquire は即座に戻り、空きが無ければ release まで待つ。"""
    order: list[str] = []

    async def main() -> None:
        sem = asyncio.Semaphore(1)
        assert await sem.acquire() is True
        assert sem.locked() is True

        async def waiter() -> None:
            order.append("waiting")
            await sem.acquire()
            order.append("acquired")

        task = asyncio.create_task(waiter())
        await asyncio.sleep(0.01)
        assert order == ["waiting"]
        sem.release()
        await task
        assert order == ["waiting", "acquired"]

    asyncio.run(main())


def test_all_waiters_complete_after_release() -> None:
    """release() すると待機中の全タスクが（順序は問わず）完了する。"""
    order: list[int] = []

    async def main() -> None:
        sem = asyncio.Semaphore(1)
        await sem.acquire()

        async def waiter(n: int) -> None:
            async with sem:
                order.append(n)

        tasks = [asyncio.create_task(waiter(n)) for n in (3, 1, 2)]
        await asyncio.sleep(0)
        sem.release()
        await asyncio.gather(*tasks)

    asyncio.run(main())
    # 再開順は仕様で保証されない（CPython では acquire 順）。全員が完了したことだけを検証する
    assert sorted(order) == [1, 2, 3]


def test_extra_release_raises_the_limit() -> None:
    """release は初期値を超えても例外にならず、その分だけ同時実行数が増える。"""
    sem = asyncio.Semaphore(1)
    sem.release()
    running = 0
    peak = 0

    async def work() -> None:
        nonlocal running, peak
        async with sem:
            running += 1
            peak = max(peak, running)
            await asyncio.sleep(0.01)
            running -= 1

    async def main() -> None:
        await asyncio.gather(work(), work(), work())

    asyncio.run(main())
    assert peak == 2


def test_locked_reflects_availability() -> None:
    """locked() は空きが無いときだけ True。"""
    sem = asyncio.Semaphore(0)
    assert sem.locked() is True
    sem.release()
    assert sem.locked() is False


def test_cancelled_waiter_does_not_take_permit() -> None:
    """待機中の acquire がキャンセルされると CancelledError になり、permit は取得しない。"""

    async def main() -> None:
        sem = asyncio.Semaphore(1)
        await sem.acquire()
        task = asyncio.create_task(sem.acquire())
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        sem.release()
        assert sem.locked() is False

    asyncio.run(main())


def test_negative_initial_value_raises() -> None:
    """初期値に負数を渡すと ValueError。"""
    with pytest.raises(ValueError):
        asyncio.Semaphore(-1)


def test_bounded_semaphore_rejects_extra_release() -> None:
    """Alternatives: BoundedSemaphore は余分な release を ValueError で検出する。"""
    sem = asyncio.BoundedSemaphore(1)
    with pytest.raises(ValueError):
        sem.release()
