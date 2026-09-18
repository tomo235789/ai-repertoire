"""http-timeout: httpx.Timeout の Contract を検証する。"""

import socket
import socketserver
import threading
import time
import urllib.request
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import httpx
import pytest

SLOW = 0.5  # 遅延応答の秒数。テストの timeout はこれより十分短くする


class Handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/slow-headers":
            time.sleep(SLOW)
        if self.path == "/slow-body":
            self.send_response(200)
            self.send_header("Content-Length", "10")
            self.end_headers()
            self.wfile.write(b"12345")
            self.wfile.flush()
            time.sleep(SLOW)
            self.wfile.write(b"67890")
            return
        body = b'{"ok": true}'
        self.send_response(500 if self.path == "/error" else 200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args: object) -> None:
        pass


class Server(ThreadingHTTPServer):
    daemon_threads = True

    def server_bind(self) -> None:
        socketserver.TCPServer.server_bind(self)  # HTTPServer の getfqdn（逆引き DNS で数十秒かかることがある）を避ける
        self.server_name, self.server_port = "127.0.0.1", self.server_address[1]

    def handle_error(self, request: object, client_address: object) -> None:
        pass  # クライアントがタイムアウトで先に切った接続の BrokenPipeError を出力しない


@pytest.fixture(scope="module")
def base_url() -> Iterator[str]:
    server = Server(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_address[1]}"
    server.shutdown()
    server.server_close()
    thread.join()


def test_timeout_object_fields() -> None:
    """Timeout(5.0) は 4 つ全部、Timeout(5.0, connect=2.0) は connect だけ上書き。既定値なしの一部指定は ValueError。"""
    all_five = httpx.Timeout(5.0)
    assert (all_five.connect, all_five.read, all_five.write, all_five.pool) == (5.0, 5.0, 5.0, 5.0)
    mixed = httpx.Timeout(5.0, connect=2.0)
    assert (mixed.connect, mixed.read, mixed.write, mixed.pool) == (2.0, 5.0, 5.0, 5.0)
    assert httpx.Timeout(None).read is None
    with pytest.raises(ValueError):
        httpx.Timeout(connect=2.0)


def test_default_is_five_seconds() -> None:
    """timeout= を省略すると既定は 5 秒。"""
    with httpx.Client() as client:
        assert client.timeout == httpx.Timeout(5.0)


def test_completes_within_timeout(base_url: str) -> None:
    """時間内に終われば Response がそのまま返る。"""
    response = httpx.get(f"{base_url}/fast", timeout=httpx.Timeout(5.0, connect=2.0))
    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_slow_headers_raise_read_timeout(base_url: str) -> None:
    """ヘッダーが read 秒以内に届かなければ ReadTimeout。TimeoutException / TransportError のサブクラス。"""
    with pytest.raises(httpx.ReadTimeout) as info:
        httpx.get(f"{base_url}/slow-headers", timeout=httpx.Timeout(0.05, connect=2.0))
    assert isinstance(info.value, httpx.TimeoutException)
    assert isinstance(info.value, httpx.TransportError)
    assert str(info.value) == "timed out"


def test_read_timeout_applies_between_body_chunks(base_url: str) -> None:
    """read はデータが届かない区間ごとに数える。本文の途中で止まっても ReadTimeout。"""
    with pytest.raises(httpx.ReadTimeout):
        httpx.get(f"{base_url}/slow-body", timeout=httpx.Timeout(0.05))


def test_none_means_no_limit(base_url: str) -> None:
    """timeout=None なら制限無しで、遅い応答も待ち切る。"""
    response = httpx.get(f"{base_url}/slow-headers", timeout=None)
    assert response.status_code == 200


def test_connect_timeout_is_separate_class() -> None:
    """接続が connect 秒以内に確立しなければ ConnectTimeout。

    実際に接続を待たせる相手は環境依存（到達不能アドレスやプロキシの有無で変わる）なので、
    ここでは transport が ConnectTimeout を出したときの型と伝わり方だけを決定的に検証する。
    """
    assert issubclass(httpx.ConnectTimeout, httpx.TimeoutException)
    assert issubclass(httpx.ReadTimeout, httpx.TimeoutException)
    assert not issubclass(httpx.ConnectError, httpx.TimeoutException)

    def raise_connect_timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectTimeout("connect timed out", request=request)

    client = httpx.Client(transport=httpx.MockTransport(raise_connect_timeout))
    with pytest.raises(httpx.TimeoutException) as exc:
        client.get("http://127.0.0.1/")
    assert isinstance(exc.value, httpx.ConnectTimeout)


def test_connection_refused_is_not_timeout() -> None:
    """接続拒否は ConnectError で、TimeoutException ではない。"""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        free_port = probe.getsockname()[1]
    with pytest.raises(httpx.ConnectError) as info:
        httpx.get(f"http://127.0.0.1:{free_port}/", timeout=httpx.Timeout(1.0))
    assert not isinstance(info.value, httpx.TimeoutException)


def test_error_status_does_not_raise(base_url: str) -> None:
    """4xx / 5xx は例外にならず Response が返る。"""
    response = httpx.get(f"{base_url}/error", timeout=httpx.Timeout(5.0))
    assert response.status_code == 500


def test_client_default_and_per_request_override(base_url: str) -> None:
    """Client の timeout を既定にし、リクエストごとに上書きできる。"""
    with httpx.Client(timeout=httpx.Timeout(0.05)) as client:
        with pytest.raises(httpx.ReadTimeout):
            client.get(f"{base_url}/slow-headers")
        assert client.get(f"{base_url}/slow-headers", timeout=5.0).status_code == 200


def test_urllib_alternative_raises_builtin_timeout_error(base_url: str) -> None:
    """Alternatives: urllib.request.urlopen(timeout=) は組み込みの TimeoutError を投げる。"""
    with pytest.raises(TimeoutError):
        urllib.request.urlopen(f"{base_url}/slow-headers", timeout=0.05)
