"""async-timeout: asyncio.timeout の Contract を検証する。"""

import asyncio

import pytest


def test_raises_timeout_error_and_cancels_inner_work() -> None:
    """delay 以内に終わらなければ中の処理をキャンセルしてから TimeoutError を送出し、残りは実行されない。"""
    events: list[str] = []

    async def slow() -> None:
        try:
            await asyncio.sleep(10)
            events.append("finished")
        except asyncio.CancelledError:
            events.append("cancelled")
            raise

    async def main() -> None:
        with pytest.raises(TimeoutError):
            async with asyncio.timeout(0.01) as tm:
                await slow()
                events.append("after")
        assert tm.expired() is True

    asyncio.run(main())
    assert events == ["cancelled"]


def test_timeout_error_is_builtin() -> None:
    """TimeoutError は組み込みの TimeoutError で、asyncio.TimeoutError と同一。"""
    assert asyncio.TimeoutError is TimeoutError

    async def main() -> None:
        with pytest.raises(TimeoutError) as info:
            async with asyncio.timeout(0.01):
                await asyncio.sleep(10)
        assert type(info.value) is TimeoutError

    asyncio.run(main())


def test_completes_in_time() -> None:
    """時間内に終わればブロックの結果がそのまま使え、expired() は False。"""

    async def main() -> None:
        async with asyncio.timeout(1) as tm:
            value = await asyncio.sleep(0, result="ok")
        assert value == "ok"
        assert tm.expired() is False

    asyncio.run(main())


def test_other_exceptions_pass_through() -> None:
    """ブロックの中の TimeoutError 以外の例外はそのまま伝わる。"""

    async def main() -> None:
        with pytest.raises(ValueError, match="inner"):
            async with asyncio.timeout(1):
                raise ValueError("inner")

    asyncio.run(main())


def test_zero_negative_and_none_delay() -> None:
    """0 以下の delay はブロックの中で await した時点で TimeoutError、None は制限無し。"""

    async def main() -> None:
        with pytest.raises(TimeoutError):
            async with asyncio.timeout(0):
                await asyncio.sleep(0)
        with pytest.raises(TimeoutError):
            async with asyncio.timeout(-1):
                await asyncio.sleep(0)
        async with asyncio.timeout(None) as tm:
            await asyncio.sleep(0.001)
        assert tm.when() is None
        assert tm.expired() is False

    asyncio.run(main())


def test_reschedule_and_when() -> None:
    """reschedule で締め切りを延ばせ、when() で現在の締め切りを確認できる。"""

    async def main() -> None:
        loop = asyncio.get_running_loop()
        async with asyncio.timeout(0.005) as tm:
            original = tm.when()
            assert original is not None
            tm.reschedule(loop.time() + 0.05)
            assert tm.when() is not None
            assert tm.when() > original
            await asyncio.sleep(0.01)
        assert tm.expired() is False

    asyncio.run(main())


def test_context_manager_cannot_be_reused() -> None:
    """コンテキストマネージャは 1 回しか使えず、2 回目の async with は RuntimeError。"""

    async def main() -> None:
        tm = asyncio.timeout(1)
        async with tm:
            pass
        with pytest.raises(RuntimeError):
            async with tm:
                pass

    asyncio.run(main())


def test_wait_for_alternative_raises_same_error() -> None:
    """Alternatives: wait_for も超過時は組み込みの TimeoutError を送出する。"""

    async def main() -> None:
        with pytest.raises(TimeoutError):
            await asyncio.wait_for(asyncio.sleep(10), timeout=0.01)

    asyncio.run(main())


def test_swallowed_cancellation_prevents_timeout_error() -> None:
    """Pitfalls: 中の処理が CancelledError を握りつぶすと TimeoutError にならない。"""
    events: list[str] = []

    async def main() -> None:
        async with asyncio.timeout(0.01) as tm:
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                events.append("swallowed")
            events.append("continued")
        assert tm.expired() is True

    asyncio.run(main())
    assert events == ["swallowed", "continued"]


def test_outer_cancellation_stays_cancelled_error() -> None:
    """Pitfalls: 外側でタスク自体がキャンセルされた場合は CancelledError のまま伝わる。"""

    async def guarded() -> None:
        async with asyncio.timeout(1):
            await asyncio.sleep(10)

    async def main() -> None:
        task = asyncio.create_task(guarded())
        await asyncio.sleep(0)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(main())
