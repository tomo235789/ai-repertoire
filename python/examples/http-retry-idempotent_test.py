"""http-retry-idempotent: tenacity.retry + httpx の Contract を検証する。"""

from collections.abc import Callable

import httpx
import pytest
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_fixed,
)

RETRY_ON = retry_if_exception_type(httpx.TransportError) | retry_if_result(lambda r: r.status_code >= 500)


def make_client(handler: Callable[[httpx.Request], httpx.Response]) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_retries_transport_error_and_5xx_then_returns_response() -> None:
    """通信エラーと 5xx を再試行し、5xx 未満の Response が返った時点でそれを返す。"""
    calls: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(request.method)
        if len(calls) == 1:
            raise httpx.ConnectError("refused", request=request)
        if len(calls) == 2:
            return httpx.Response(503, text="busy")
        return httpx.Response(200, json={"id": 1})

    client = make_client(handler)

    @retry(retry=RETRY_ON, stop=stop_after_attempt(4), wait=wait_fixed(0), reraise=True)
    def get_item() -> httpx.Response:
        return client.get("https://example.com/items/1")

    response = get_item()
    assert response.status_code == 200
    assert response.json() == {"id": 1}
    assert calls == ["GET", "GET", "GET"]


def test_4xx_is_returned_without_retry() -> None:
    """4xx は再試行せず、その Response をそのまま返す。"""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(404)

    client = make_client(handler)

    @retry(retry=RETRY_ON, stop=stop_after_attempt(4), wait=wait_fixed(0), reraise=True)
    def get_item() -> httpx.Response:
        return client.get("https://example.com/items/1")

    assert get_item().status_code == 404
    assert calls == [1]


def test_exhausted_by_5xx_raises_retry_error_even_with_reraise() -> None:
    """最後の試行が 5xx のレスポンスなら reraise=True でも RetryError で、last_attempt.result() がその Response。"""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(502)

    client = make_client(handler)

    @retry(retry=RETRY_ON, stop=stop_after_attempt(3), wait=wait_fixed(0), reraise=True)
    def get_item() -> httpx.Response:
        return client.get("https://example.com/items/1")

    with pytest.raises(RetryError) as info:
        get_item()
    assert info.value.last_attempt.failed is False
    assert info.value.last_attempt.result().status_code == 502
    assert len(calls) == 3


def test_exhausted_by_exception_reraises_original_with_reraise() -> None:
    """最後の試行が例外なら reraise=True で元の TransportError をそのまま投げる。"""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        raise httpx.ReadTimeout("timed out", request=request)

    client = make_client(handler)

    @retry(retry=RETRY_ON, stop=stop_after_attempt(3), wait=wait_fixed(0), reraise=True)
    def get_item() -> httpx.Response:
        return client.get("https://example.com/items/1")

    with pytest.raises(httpx.ReadTimeout):
        get_item()
    assert len(calls) == 3


def test_exhausted_by_exception_without_reraise_wraps_in_retry_error() -> None:
    """reraise を付けないと例外でも RetryError に包まれ、last_attempt.exception() から取り出せる。"""

    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("refused", request=request)

    client = make_client(handler)

    @retry(retry=RETRY_ON, stop=stop_after_attempt(2), wait=wait_fixed(0))
    def get_item() -> httpx.Response:
        return client.get("https://example.com/items/1")

    with pytest.raises(RetryError) as info:
        get_item()
    assert isinstance(info.value.last_attempt.exception(), httpx.ConnectError)


def test_exception_hierarchy() -> None:
    """ConnectError / TimeoutException は TransportError のサブクラスで、HTTPStatusError は違う。"""
    assert issubclass(httpx.ConnectError, httpx.TransportError)
    assert issubclass(httpx.ConnectTimeout, httpx.TransportError)
    assert issubclass(httpx.ReadTimeout, httpx.TransportError)
    assert not issubclass(httpx.HTTPStatusError, httpx.TransportError)


def test_response_is_returned_regardless_of_status_until_raise_for_status() -> None:
    """httpx はステータスに関わらず Response を返し、raise_for_status() で初めて HTTPStatusError になる。"""
    client = make_client(lambda request: httpx.Response(500))
    response = client.get("https://example.com/items/1")
    assert response.status_code == 500
    with pytest.raises(httpx.HTTPStatusError):
        response.raise_for_status()


def test_non_matching_exception_is_raised_immediately() -> None:
    """TransportError 以外の例外（HTTPStatusError など）は再試行せずそのまま投げる。"""
    calls: list[int] = []

    def handler(request: httpx.Request) -> httpx.Response:
        calls.append(1)
        return httpx.Response(500)

    client = make_client(handler)

    @retry(retry=RETRY_ON, stop=stop_after_attempt(3), wait=wait_fixed(0), reraise=True)
    def get_item() -> httpx.Response:
        return client.get("https://example.com/items/1").raise_for_status()

    with pytest.raises(httpx.HTTPStatusError):
        get_item()
    assert calls == [1]


def test_same_body_is_sent_on_each_attempt() -> None:
    """json= で渡した本文は試行ごとに同じ内容で送り直される。"""
    bodies: list[bytes] = []

    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(request.content)
        return httpx.Response(503) if len(bodies) < 2 else httpx.Response(200)

    client = make_client(handler)

    @retry(retry=RETRY_ON, stop=stop_after_attempt(3), wait=wait_fixed(0), reraise=True)
    def put_item() -> httpx.Response:
        return client.put("https://example.com/items/1", json={"name": "a"})

    assert put_item().status_code == 200
    assert bodies == [b'{"name":"a"}', b'{"name":"a"}']
