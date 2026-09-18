"""error-invariant: assert 文の Contract を検証する。

PYTEST_DONT_REWRITE: pytest の assert 書き換えを止め、素の AssertionError のメッセージを検証する。
"""

import os
import subprocess
import sys
import textwrap
import warnings

import pytest


def total(prices: list[float] | None) -> float:
    """カードの Usage と同じ関数。"""
    assert prices is not None, "prices は呼び出し側で解決済みのはず"
    return sum(prices)


def parse_port(text: str) -> int:
    port = int(text)
    if not 0 < port < 65536:
        raise ValueError(f"port out of range: {port}")
    return port


def test_true_condition_passes_and_narrows() -> None:
    """条件が真なら何も起きず、以降は絞り込まれた型として使える。"""
    assert total([1.0, 2.0]) == 3.0


def test_false_condition_raises_assertion_error_with_message() -> None:
    """偽なら AssertionError で、str が message、args が (message,)。Exception のサブクラス。"""
    with pytest.raises(AssertionError) as info:
        total(None)
    assert str(info.value) == "prices は呼び出し側で解決済みのはず"
    assert info.value.args == ("prices は呼び出し側で解決済みのはず",)
    assert isinstance(info.value, Exception)


def test_message_omitted_and_message_evaluated_lazily() -> None:
    """message を省くと str は ''。message は失敗したときだけ評価される。"""
    with pytest.raises(AssertionError) as info:
        assert False  # noqa: B011
    assert str(info.value) == ""
    assert info.value.args == ()
    evaluated: list[int] = []

    def message() -> str:
        evaluated.append(1)
        return "never"

    assert True, message()  # noqa: B011
    assert evaluated == []


def run_python(code: str, *flags: str, env_extra: dict[str, str] | None = None) -> str:
    env = {**os.environ, **(env_extra or {})}
    env.pop("PYTHONOPTIMIZE", None) if env_extra is None else None
    result = subprocess.run([sys.executable, *flags, "-c", textwrap.dedent(code)], capture_output=True, text=True, check=True, env=env)
    return result.stdout.strip()


PROBE = """
    evaluated = []
    def cond():
        evaluated.append("cond")
        return False
    def msg():
        evaluated.append("msg")
        return "m"
    try:
        assert cond(), msg()
        print("passed", __debug__, evaluated)
    except AssertionError as e:
        print("raised", __debug__, evaluated)
"""


def test_optimize_flag_removes_assert_entirely() -> None:
    """python -O / -OO / PYTHONOPTIMIZE=1 では assert 文ごと消え、条件も message も評価されず __debug__ は False。"""
    assert run_python(PROBE) == "raised True ['cond', 'msg']"
    assert run_python(PROBE, "-O") == "passed False []"
    assert run_python(PROBE, "-OO") == "passed False []"
    assert run_python(PROBE, env_extra={"PYTHONOPTIMIZE": "1"}) == "passed False []"


def test_tuple_assertion_is_always_true_with_warning() -> None:
    """assert (cond, "msg") は常に真で、SyntaxWarning が出る。"""
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        compile("assert (False, 'msg')", "<test>", "exec")
    assert any("assertion is always true" in str(w.message) for w in caught)


def test_input_validation_uses_value_error() -> None:
    """Alternatives: 外部入力の検証は ValueError を投げる関数にする（-O でも消えない）。"""
    assert parse_port("8080") == 8080
    with pytest.raises(ValueError, match="port out of range: 70000"):
        parse_port("70000")
    code = """
        def parse_port(text):
            port = int(text)
            if not 0 < port < 65536:
                raise ValueError(f"port out of range: {port}")
            return port
        try:
            parse_port("70000")
        except ValueError as e:
            print("ValueError:", e)
    """
    assert run_python(code, "-O") == "ValueError: port out of range: 70000"


def test_falsy_values_are_rejected_by_bare_assert() -> None:
    """Pitfalls: assert value は 0 / '' / [] も弾く。is not None と明示する。"""
    for value in (0, "", []):
        with pytest.raises(AssertionError):
            assert value, "falsy"
        assert value is not None
