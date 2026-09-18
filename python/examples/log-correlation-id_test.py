"""log-correlation-id: contextvars.ContextVar の Contract を検証する。"""

import asyncio
import contextvars
import io
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from contextvars import ContextVar

import pytest

request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


class RequestIdFilter(logging.Filter):
    """カードの Usage と同じクラス。"""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id.get()
        return True


def test_get_set_reset_and_token_reuse() -> None:
    """get は default、set は Token を返し、reset で戻る。Token の再利用は RuntimeError。"""
    assert request_id.get() is None
    token = request_id.set("req-1")
    assert request_id.get() == "req-1"
    request_id.reset(token)
    assert request_id.get() is None
    with pytest.raises(RuntimeError):
        request_id.reset(token)


def test_no_default_raises_lookup_error() -> None:
    """default 無しで未設定なら LookupError。get(fallback) で引数側の既定値を使える。"""
    var: ContextVar[str] = ContextVar("no_default")
    with pytest.raises(LookupError):
        var.get()
    assert var.get("fallback") == "fallback"


def test_tasks_get_copy_of_context_at_creation() -> None:
    """create_task / gather のタスクは作成時点のコピーを持ち、中の set は親に漏れず、親のその後の set も見えない。"""

    async def handle(i: int) -> str | None:
        request_id.set(f"req-{i}")
        await asyncio.sleep(0.001 * (3 - i))
        return request_id.get()

    async def child() -> str | None:
        await asyncio.sleep(0)
        return request_id.get()

    async def main() -> None:
        token = request_id.set("outer")
        try:
            assert await asyncio.gather(*(handle(i) for i in range(3))) == ["req-0", "req-1", "req-2"]
            assert request_id.get() == "outer"
            task = asyncio.create_task(child())
            request_id.set("changed-after-create")
            assert await task == "outer"
        finally:
            request_id.reset(token)

    asyncio.run(main())
    assert request_id.get() is None


def test_direct_await_shares_context() -> None:
    """await coro() と直接待つとコンテキストを共有し、呼んだ先の set が呼び元にも見える。"""

    async def setter() -> None:
        request_id.set("from-callee")

    async def main() -> str | None:
        await setter()
        return request_id.get()

    assert asyncio.run(main()) == "from-callee"


def test_threads_do_not_inherit_but_copy_context_run_does() -> None:
    """Thread / ThreadPoolExecutor / run_in_executor には伝播せず default。copy_context().run と to_thread なら見える。"""
    token = request_id.set("req-t")
    try:
        seen: list[str | None] = []
        thread = threading.Thread(target=lambda: seen.append(request_id.get()))
        thread.start()
        thread.join()
        thread = threading.Thread(target=contextvars.copy_context().run, args=(lambda: seen.append(request_id.get()),))
        thread.start()
        thread.join()
        assert seen == [None, "req-t"]
        with ThreadPoolExecutor(max_workers=1) as pool:
            assert pool.submit(request_id.get).result() is None
            assert pool.submit(contextvars.copy_context().run, request_id.get).result() == "req-t"

        async def main() -> tuple[str | None, str | None]:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, request_id.get), await asyncio.to_thread(request_id.get)

        assert asyncio.run(main()) == (None, "req-t")
    finally:
        request_id.reset(token)


def test_logging_filter_embeds_request_id() -> None:
    """Filter で record.request_id を付けると %(request_id)s で出せる。"""
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(logging.Formatter("%(request_id)s %(message)s"))
    handler.addFilter(RequestIdFilter())
    logger = logging.getLogger("app.correlation")
    logger.handlers[:] = [handler]
    logger.propagate = False
    token = request_id.set("req-9")
    logger.warning("hello")
    request_id.reset(token)
    logger.warning("bye")
    logger.handlers[:] = []
    assert buffer.getvalue().splitlines() == ["req-9 hello", "None bye"]


def test_mutable_value_is_shared_by_reference() -> None:
    """Pitfalls: 可変オブジェクトを set すると、タスク間で参照が共有され中の変更が漏れる。"""
    shared: ContextVar[dict[str, str]] = ContextVar("shared")

    async def mutate() -> None:
        shared.get()["k"] = "changed"

    async def main() -> dict[str, str]:
        shared.set({"k": "original"})
        await asyncio.create_task(mutate())
        return shared.get()

    assert asyncio.run(main()) == {"k": "changed"}
