"""http-rate-limit-backoff: wait_exponential_jitter と Retry-After 優先の wait の Contract を検証する。"""

import random
from datetime import datetime, timedelta, timezone
from email.utils import format_datetime, parsedate_to_datetime

import httpx
import pytest
from tenacity import (
    Future,
    RetryCallState,
    RetryError,
    retry,
    retry_if_result,
    stop_after_attempt,
    stop_after_delay,
    wait_exponential_jitter,
)


def wait_retry_after(state: RetryCallState) -> float:
    """カードの Usage と同じ関数。"""
    header = state.outcome.result().headers.get("Retry-After") if state.outcome and not state.outcome.failed else None
    if header:
        if header.strip().isdigit():
            return float(header)
        when = parsedate_to_datetime_or_none(header)  # RFC 9110 の HTTP-date 形式
        if when is not None:
            return max(0.0, (when - datetime.now(timezone.utc)).total_seconds())
    return wait_exponential_jitter(initial=1, max=30, jitter=1)(state)


def parsedate_to_datetime_or_none(value: str) -> datetime | None:
    """HTTP-date を aware datetime にする。解析できなければ None。"""
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def state_with_attempt(attempt_number: int) -> RetryCallState:
    state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
    state.attempt_number = attempt_number
    return state


def _outcome(response: httpx.Response):
    """tenacity の outcome（成功扱い）を作る。"""
    future = Future(attempt_number=1)
    future.set_result(response)
    return future


def test_exponential_sequence_without_jitter() -> None:
    """jitter=0 なら initial * exp_base ** (attempt_number - 1) で、max を超えない。"""
    wait = wait_exponential_jitter(initial=1, max=30, jitter=0)
    assert [wait(state_with_attempt(n)) for n in range(1, 8)] == [1, 2, 4, 8, 16, 30, 30]


def test_jitter_is_added_before_cap() -> None:
    """ジッターは uniform(0, jitter) を足し、max はその後に適用される。"""
    wait = wait_exponential_jitter(initial=1, max=5, jitter=1)
    random.seed(0)
    first = [wait(state_with_attempt(1)) for _ in range(50)]
    assert all(1 <= w <= 2 for w in first)
    assert len(set(first)) > 1
    assert all(wait(state_with_attempt(10)) == 5 for _ in range(50))


def test_retry_after_header_is_preferred_and_case_insensitive() -> None:
    """Retry-After があればその秒数、無ければ指数バックオフ。ヘッダ名は大文字小文字を区別しない。"""
    calls: list[int] = []
    responses = [
        httpx.Response(429, headers={"retry-after": "2"}),
        httpx.Response(503),
        httpx.Response(429, headers={"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}),
        httpx.Response(200, json={"items": []}),
    ]

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return responses[len(calls) - 1]

    client = httpx.Client(transport=httpx.MockTransport(handler))
    sleeps: list[float] = []
    random.seed(0)

    @retry(retry=retry_if_result(lambda r: r.status_code in (429, 503)), wait=wait_retry_after, stop=stop_after_delay(120), sleep=sleeps.append)
    def list_items() -> httpx.Response:
        return client.get("https://example.com/items")

    assert list_items().status_code == 200
    assert len(calls) == 4
    assert sleeps[0] == 2.0
    assert 2 <= sleeps[1] <= 3  # 2 回目: 1 * 2 ** 1 + jitter
    assert sleeps[2] == 0.0  # 3 回目: 過去の HTTP 日付は残り時間 0 に丸める


def test_http_date_can_be_parsed() -> None:
    """Retry-After の HTTP 日付は email.utils.parsedate_to_datetime で aware な datetime になる。"""
    parsed = parsedate_to_datetime("Wed, 21 Oct 2015 07:28:00 GMT")
    assert parsed.isoformat() == "2015-10-21T07:28:00+00:00"


def test_future_http_date_becomes_remaining_seconds() -> None:
    """未来の HTTP 日付は「今からの残り秒数」になる（過去なら 0）。"""
    future = datetime.now(timezone.utc) + timedelta(seconds=30)
    state = state_with_attempt(1)
    state.outcome = _outcome(httpx.Response(429, headers={"Retry-After": format_datetime(future, usegmt=True)}))
    assert 25 <= wait_retry_after(state) <= 30
    state.outcome = _outcome(httpx.Response(429, headers={"Retry-After": "Wed, 21 Oct 2015 07:28:00 GMT"}))
    assert wait_retry_after(state) == 0.0


def test_only_429_and_503_are_retried() -> None:
    """retry_if_result で 429 / 503 に限定すると、他のステータスは 1 回で返る。"""
    for status in (200, 404, 500):
        calls: list[int] = []

        def handler(request: httpx.Request, status: int = status, calls: list[int] = calls) -> httpx.Response:
            calls.append(1)
            return httpx.Response(status)

        client = httpx.Client(transport=httpx.MockTransport(handler))

        @retry(retry=retry_if_result(lambda r: r.status_code in (429, 503)), wait=wait_retry_after, stop=stop_after_attempt(5), sleep=lambda s: None)
        def list_items() -> httpx.Response:
            return client.get("https://example.com/items")

        assert list_items().status_code == status
        assert calls == [1]


def test_stop_after_delay_uses_elapsed_time() -> None:
    """stop_after_delay は最初の試行からの実経過秒で判定する。"""
    stop = stop_after_delay(10)
    state = RetryCallState(None, None, (), {})  # type: ignore[arg-type]
    state.set_result(httpx.Response(429))
    assert state.seconds_since_start is not None
    assert stop(state) is False
    state.outcome_timestamp = state.start_time + 10
    assert stop(state) is True


def test_exhausted_raises_retry_error_with_last_response() -> None:
    """使い切ると RetryError で、last_attempt.result() が最後の Response。"""
    client = httpx.Client(transport=httpx.MockTransport(lambda request: httpx.Response(429, headers={"Retry-After": "1"})))
    sleeps: list[float] = []

    @retry(retry=retry_if_result(lambda r: r.status_code in (429, 503)), wait=wait_retry_after, stop=stop_after_attempt(3), sleep=sleeps.append)
    def list_items() -> httpx.Response:
        return client.get("https://example.com/items")

    with pytest.raises(RetryError) as info:
        list_items()
    assert info.value.last_attempt.result().status_code == 429
    assert sleeps == [1.0, 1.0]


def test_async_function_uses_injected_sleep_too() -> None:
    """async def でも同じ wait が使え、sleep= に async 関数を注入できる。"""
    import asyncio

    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(429, headers={"Retry-After": "3"}) if len(calls) < 2 else httpx.Response(200)

    sleeps: list[float] = []

    async def record(seconds: float) -> None:
        sleeps.append(seconds)

    async def main() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:

            @retry(retry=retry_if_result(lambda r: r.status_code in (429, 503)), wait=wait_retry_after, stop=stop_after_attempt(5), sleep=record)
            async def list_items() -> httpx.Response:
                return await client.get("https://example.com/items")

            assert (await list_items()).status_code == 200

    asyncio.run(main())
    assert sleeps == [3.0]
