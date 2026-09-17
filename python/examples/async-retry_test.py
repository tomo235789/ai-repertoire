"""async-retry: tenacity.retry の Contract を検証する。"""

import asyncio
import inspect

import pytest
from tenacity import (
    RetryCallState,
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_fixed,
)


def test_retries_until_success_and_returns_value() -> None:
    """例外が出たら再実行し、正常に返った時点でその値を返す。"""
    calls: list[int] = []

    @retry(stop=stop_after_attempt(5), wait=wait_fixed(0))
    def flaky() -> str:
        calls.append(1)
        if len(calls) < 3:
            raise ConnectionError("transient")
        return "ok"

    assert flaky() == "ok"
    assert len(calls) == 3


def test_stop_after_attempt_counts_total_attempts() -> None:
    """stop_after_attempt(n) は初回を含む合計の試行回数。"""
    calls: list[int] = []

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0))
    def always_fail() -> None:
        calls.append(1)
        raise ConnectionError("down")

    with pytest.raises(RetryError):
        always_fail()
    assert len(calls) == 3


def test_retry_error_wraps_last_exception_by_default() -> None:
    """上限に達すると RetryError を投げ、元の例外は last_attempt.exception() から取り出せる。"""

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(0))
    def always_fail() -> None:
        raise ConnectionError("down")

    with pytest.raises(RetryError) as info:
        always_fail()
    original = info.value.last_attempt.exception()
    assert isinstance(original, ConnectionError)
    assert str(original) == "down"
    assert info.value.last_attempt.attempt_number == 2


def test_reraise_raises_original_exception() -> None:
    """reraise=True なら最後の試行の元の例外をそのまま投げる。"""
    calls: list[int] = []

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(0), reraise=True)
    def always_fail() -> None:
        calls.append(1)
        raise ConnectionError("down")

    with pytest.raises(ConnectionError, match="down"):
        always_fail()
    assert len(calls) == 2


def test_non_matching_exception_is_raised_immediately() -> None:
    """retry_if_exception_type に合わない例外は再試行せず、その場でそのまま投げる。"""
    calls: list[int] = []

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0), retry=retry_if_exception_type(ConnectionError))
    def wrong_error() -> None:
        calls.append(1)
        raise KeyError("missing")

    with pytest.raises(KeyError):
        wrong_error()
    assert len(calls) == 1


def test_default_retries_any_exception_but_not_base_exception() -> None:
    """retry を省略すると Exception のサブクラスすべてを再試行し、BaseException は捕捉しない。"""
    calls: list[str] = []

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(0))
    def raises_value_error() -> None:
        calls.append("value")
        raise ValueError("v")

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(0))
    def raises_interrupt() -> None:
        calls.append("interrupt")
        raise KeyboardInterrupt

    with pytest.raises(RetryError):
        raises_value_error()
    with pytest.raises(KeyboardInterrupt):
        raises_interrupt()
    assert calls == ["value", "value", "interrupt"]


def test_before_sleep_is_called_before_each_wait() -> None:
    """before_sleep は再試行の待機前に毎回呼ばれ、試行番号・例外・待ち時間を読める。最後の試行後は呼ばれない。"""
    seen: list[tuple[int, str, float]] = []

    def record(state: RetryCallState) -> None:
        assert state.outcome is not None
        assert state.next_action is not None
        seen.append((state.attempt_number, type(state.outcome.exception()).__name__, state.next_action.sleep))

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0.001), before_sleep=record)
    def always_fail() -> None:
        raise ConnectionError("down")

    with pytest.raises(RetryError):
        always_fail()
    assert seen == [(1, "ConnectionError", 0.001), (2, "ConnectionError", 0.001)]


def test_async_function_keeps_event_loop_running() -> None:
    """async def に付けても async def のままで、待機中はほかのタスクが動く。"""
    order: list[str] = []

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(0.02))
    async def flaky() -> str:
        order.append("try")
        if order.count("try") < 2:
            raise ConnectionError("transient")
        return "ok"

    async def other() -> None:
        await asyncio.sleep(0.005)
        order.append("other")

    assert inspect.iscoroutinefunction(flaky)

    async def main() -> None:
        results = await asyncio.gather(flaky(), other())
        assert results[0] == "ok"

    asyncio.run(main())
    assert order == ["try", "other", "try"]


def test_async_function_raises_retry_error_when_exhausted() -> None:
    """async def でも上限に達すると RetryError になる。"""
    calls: list[int] = []

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(0))
    async def always_fail() -> None:
        calls.append(1)
        raise ConnectionError("down")

    async def main() -> None:
        with pytest.raises(RetryError):
            await always_fail()

    asyncio.run(main())
    assert len(calls) == 2


def test_retry_error_callback_returns_default() -> None:
    """Alternatives: retry_error_callback で使い切ったときに既定値を返せる。"""

    @retry(stop=stop_after_attempt(2), wait=wait_fixed(0), retry_error_callback=lambda state: "fallback")
    def always_fail() -> str:
        raise ConnectionError("down")

    assert always_fail() == "fallback"
