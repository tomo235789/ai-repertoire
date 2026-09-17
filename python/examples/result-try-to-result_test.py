"""result-try-to-result: returns.result.safe の Contract を検証する。"""

import asyncio
import json

import pytest
from returns.primitives.exceptions import UnwrapFailedError
from returns.result import Failure, Result, Success, safe


@safe
def parse(text: str) -> dict:
    return json.loads(text)


def test_success_and_failure() -> None:
    """正常に返れば Success(戻り値)、例外なら Failure(例外オブジェクト)。None も Success(None)。"""
    ok = parse('{"ok": true}')
    bad = parse("{oops")
    assert isinstance(ok, Success)
    assert isinstance(ok, Result)
    assert ok.unwrap() == {"ok": True}
    assert isinstance(bad, Failure)
    assert isinstance(bad.failure(), json.JSONDecodeError)

    @safe
    def nothing() -> None:
        return None

    assert nothing() == Success(None)


def test_function_is_called_once_immediately() -> None:
    """装飾された関数を呼ぶと即座に元の関数を 1 回実行する。"""
    calls: list[int] = []

    @safe
    def record() -> int:
        calls.append(1)
        return 1

    assert record() == Success(1)
    assert calls == [1]


def test_base_exception_passes_through() -> None:
    """Exception のサブクラスだけ捕捉し、KeyboardInterrupt / SystemExit は捕捉しない。"""

    @safe
    def interrupt() -> None:
        raise KeyboardInterrupt

    @safe
    def exit_now() -> None:
        raise SystemExit(3)

    with pytest.raises(KeyboardInterrupt):
        interrupt()
    with pytest.raises(SystemExit):
        exit_now()


def test_exceptions_argument_narrows_what_is_caught() -> None:
    """safe(exceptions=...) で捕捉する例外を絞れ、それ以外はそのまま伝わる。"""

    @safe(exceptions=(ValueError,))
    def pick(n: int) -> int:
        if n == 1:
            raise ValueError("v")
        if n == 2:
            raise KeyError("k")
        return n

    assert isinstance(pick(1).failure(), ValueError)
    with pytest.raises(KeyError):
        pick(2)
    assert pick(3) == Success(3)


def test_match_and_truthiness() -> None:
    """match の case Success / Failure で判別でき、Failure も真偽値は True。"""
    seen: list[str] = []
    for result in (parse('{"a": 1}'), parse("{oops")):
        match result:
            case Success(value):
                seen.append(f"success:{value['a']}")
            case Failure(err):
                seen.append(f"failure:{type(err).__name__}")
    assert seen == ["success:1", "failure:JSONDecodeError"]
    assert bool(parse("{oops")) is True


def test_unwrap_value_or_and_failure() -> None:
    """unwrap は Failure で UnwrapFailedError（__cause__ に元の例外）、value_or は既定値、failure は Success で UnwrapFailedError。"""
    ok = parse('{"ok": true}')
    bad = parse("{oops")
    assert ok.value_or({}) == {"ok": True}
    assert bad.value_or({}) == {}
    with pytest.raises(UnwrapFailedError) as info:
        bad.unwrap()
    assert isinstance(info.value.__cause__, json.JSONDecodeError)
    with pytest.raises(UnwrapFailedError):
        ok.failure()


def test_map_transforms_only_success() -> None:
    """map は Success の中身だけを変換し、Failure はそのまま通す。"""
    assert parse('{"ok": true}').map(lambda d: d["ok"]) == Success(True)
    mapped = parse("{oops").map(lambda d: d["ok"])
    assert isinstance(mapped, Failure)
    assert isinstance(mapped.failure(), json.JSONDecodeError)


def test_async_function_is_not_protected() -> None:
    """Alternatives: async def に付けるとコルーチンが Success に包まれ、例外は捕捉されない。"""

    @safe
    async def fail() -> None:
        raise ValueError("async")

    result = fail()
    assert isinstance(result, Success)
    coroutine = result.unwrap()
    assert asyncio.iscoroutine(coroutine)

    async def main() -> None:
        with pytest.raises(ValueError, match="async"):
            await coroutine

    asyncio.run(main())


def test_failure_equality_uses_exception_identity() -> None:
    """Pitfalls: 別々に作った同じ内容の例外を包んだ Failure は等しくならない。"""
    assert Failure(ValueError("x")) != Failure(ValueError("x"))
    err = ValueError("x")
    assert Failure(err) == Failure(err)
