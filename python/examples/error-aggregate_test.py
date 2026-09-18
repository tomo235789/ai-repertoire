"""error-aggregate: ExceptionGroup / except* の Contract を検証する。"""

import asyncio
import traceback
from builtins import BaseExceptionGroup, ExceptionGroup  # ruff の target-version 既定（3.9）でも F821 にならないよう明示する

import pytest


def make_group() -> ExceptionGroup[Exception]:
    return ExceptionGroup("2 errors", [ValueError("a"), TypeError("b")])


def test_attributes_and_str() -> None:
    """Exception のサブクラスで、message と exceptions（タプルのコピー）を持つ。"""
    errors = [ValueError("a"), TypeError("b")]
    group = ExceptionGroup("2 errors", errors)
    assert isinstance(group, Exception)
    assert group.message == "2 errors"
    assert group.exceptions == (errors[0], errors[1])
    assert isinstance(group.exceptions, tuple)
    assert str(group) == "2 errors (2 sub-exceptions)"
    errors.append(OSError("c"))
    assert len(group.exceptions) == 2


def test_constructor_validation() -> None:
    """空は ValueError、BaseException を入れると TypeError。BaseExceptionGroup は要素で型を選ぶ。"""
    with pytest.raises(ValueError):
        ExceptionGroup("x", [])
    with pytest.raises(TypeError):
        ExceptionGroup("x", [KeyboardInterrupt()])
    assert type(BaseExceptionGroup("x", [ValueError()])) is ExceptionGroup
    base = BaseExceptionGroup("x", [KeyboardInterrupt()])
    assert type(base) is BaseExceptionGroup
    assert not isinstance(base, Exception)


def test_except_star_dispatches_by_type_and_reraises_rest() -> None:
    """except* は合う例外だけのグループを渡し、合う節をすべて実行し、残りは投げ直す。"""
    seen: list[tuple[str, tuple[str, ...]]] = []
    try:
        raise ExceptionGroup("3 errors", [ValueError("a"), TypeError("b"), OSError("c")])
    except* ValueError as group:
        seen.append(("ValueError", tuple(str(e) for e in group.exceptions)))
        assert group.message == "3 errors"
    except* TypeError as group:
        seen.append(("TypeError", tuple(str(e) for e in group.exceptions)))
    except* OSError as group:
        seen.append(("OSError", tuple(str(e) for e in group.exceptions)))
    assert seen == [("ValueError", ("a",)), ("TypeError", ("b",)), ("OSError", ("c",))]

    with pytest.raises(ExceptionGroup) as info:
        try:
            raise make_group()
        except* ValueError:
            pass
    assert [type(e) for e in info.value.exceptions] == [TypeError]


def test_plain_except_does_not_catch_group() -> None:
    """except ValueError はグループを捕捉しない。except ExceptionGroup なら丸ごと捕捉する。"""
    caught: list[str] = []
    try:
        raise make_group()
    except ValueError:
        caught.append("ValueError")
    except ExceptionGroup as group:
        caught.append(f"ExceptionGroup:{len(group.exceptions)}")
    assert caught == ["ExceptionGroup:2"]


def test_subgroup_and_split() -> None:
    """subgroup は合う例外だけのグループ（無ければ None）、split は (合う, 合わない)。入れ子と message は保たれる。"""
    group = make_group()
    only_values = group.subgroup(ValueError)
    assert only_values is not None
    assert [type(e) for e in only_values.exceptions] == [ValueError]
    assert only_values.message == "2 errors"
    assert group.subgroup(KeyError) is None
    match, rest = group.split((ValueError, TypeError))
    assert match is not None and rest is None
    nested = ExceptionGroup("outer", [group, OSError("c")])
    match, rest = nested.split(lambda e: isinstance(e, OSError))
    assert match is not None and rest is not None
    assert [type(e) for e in match.exceptions] == [OSError]
    inner = rest.exceptions[0]
    assert isinstance(inner, ExceptionGroup)
    assert [type(e) for e in inner.exceptions] == [ValueError, TypeError]


def test_except_star_wraps_bare_exception_and_forbids_return() -> None:
    """except* は単独の例外も ExceptionGroup('', (e,)) に包む。節の中の return は SyntaxError。"""
    try:
        raise ValueError("solo")
    except* ValueError as group:
        assert isinstance(group, ExceptionGroup)
        assert group.message == ""
        assert len(group.exceptions) == 1
    with pytest.raises(SyntaxError):
        compile("def f():\n    try:\n        pass\n    except* ValueError:\n        return 1\n", "<test>", "exec")


def test_task_group_raises_exception_group() -> None:
    """asyncio.TaskGroup は失敗したタスクの例外を ExceptionGroup にまとめて投げる。"""

    async def fail(n: int) -> None:
        raise ValueError(str(n))

    async def main() -> list[str]:
        messages: list[str] = []
        try:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(fail(1))
                tg.create_task(fail(2))
        except* ValueError as group:  # except* の中では return できないので変数に入れる
            assert group.message == "unhandled errors in a TaskGroup"
            messages = sorted(str(e) for e in group.exceptions)
        return messages

    assert asyncio.run(main()) == ["1", "2"]


def test_traceback_is_rendered_as_tree() -> None:
    """traceback はツリー状に各例外を並べて表示する。"""
    with pytest.raises(ExceptionGroup) as info:
        raise make_group()
    text = "".join(traceback.format_exception(info.value))
    assert "ExceptionGroup: 2 errors (2 sub-exceptions)" in text
    assert "+---------------- 1 ----------------" in text
    assert "ValueError: a" in text
    assert "TypeError: b" in text
