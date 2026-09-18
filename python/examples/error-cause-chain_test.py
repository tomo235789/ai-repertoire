"""error-cause-chain: raise ... from ... の Contract を検証する。"""

import traceback

import pytest


class ConfigError(Exception): ...


def load(text: str) -> int:
    """カードの Usage と同じ関数。"""
    try:
        return int(text)
    except ValueError as err:
        raise ConfigError(f"設定を読めなかった: {text!r}") from err


def test_from_sets_cause_and_suppress_context() -> None:
    """from err は __cause__ に元の例外を付け、__suppress_context__ を True にする。__context__ も同じ例外。"""
    with pytest.raises(ConfigError) as info:
        load("x")
    err = info.value
    assert isinstance(err.__cause__, ValueError)
    assert err.__suppress_context__ is True
    assert err.__context__ is err.__cause__
    assert str(err) == "設定を読めなかった: 'x'"


def test_traceback_shows_direct_cause() -> None:
    """traceback には元の例外の後に "direct cause" の見出しを挟んで両方表示される。"""
    with pytest.raises(ConfigError) as info:
        load("x")
    text = "".join(traceback.format_exception(info.value))
    assert "ValueError: invalid literal for int()" in text
    assert "The above exception was the direct cause of the following exception:" in text
    assert text.rstrip().endswith("ConfigError: 設定を読めなかった: 'x'")
    assert "ValueError" not in "".join(traceback.format_exception(info.value, chain=False))


def test_implicit_context_without_from() -> None:
    """except の中で from 無しに raise すると __cause__ は None で __context__ が付き、"During handling" になる。"""

    def load_implicit() -> None:
        try:
            int("x")
        except ValueError:
            raise ConfigError("implicit")

    with pytest.raises(ConfigError) as info:
        load_implicit()
    assert info.value.__cause__ is None
    assert isinstance(info.value.__context__, ValueError)
    assert info.value.__suppress_context__ is False
    assert "During handling of the above exception, another exception occurred:" in "".join(traceback.format_exception(info.value))


def test_from_none_hides_context() -> None:
    """from None は __cause__ を None、__suppress_context__ を True にし、traceback に元の例外を出さない。"""

    def load_quiet() -> None:
        try:
            int("x")
        except ValueError:
            raise ConfigError("quiet") from None

    with pytest.raises(ConfigError) as info:
        load_quiet()
    assert info.value.__cause__ is None
    assert info.value.__suppress_context__ is True
    assert isinstance(info.value.__context__, ValueError)
    assert "ValueError" not in "".join(traceback.format_exception(info.value))


def test_cause_must_be_exception_or_class_or_none() -> None:
    """from の右辺は例外インスタンス・例外クラス・None のみ。それ以外は TypeError。"""
    with pytest.raises(TypeError, match="exception causes must derive from BaseException"):
        raise ConfigError("x") from "not an exception"  # type: ignore[misc]
    with pytest.raises(ConfigError) as info:
        raise ConfigError("x") from ValueError
    assert repr(info.value.__cause__) == "ValueError()"


def test_from_outside_except_has_no_context() -> None:
    """except の外でも from は使え、__context__ は None。"""
    original = ValueError("v")
    with pytest.raises(ConfigError) as info:
        raise ConfigError("x") from original
    assert info.value.__cause__ is original
    assert info.value.__context__ is None


def test_walk_to_root_cause() -> None:
    """根本原因は __cause__ を None になるまで辿る。"""

    def outer() -> None:
        try:
            load("x")
        except ConfigError as err:
            raise RuntimeError("起動に失敗") from err

    with pytest.raises(RuntimeError) as info:
        outer()
    err: BaseException = info.value
    depth = 0
    while err.__cause__ is not None:
        err = err.__cause__
        depth += 1
    assert isinstance(err, ValueError)
    assert depth == 2


def test_add_note_alternative_keeps_type_and_cause() -> None:
    """Alternatives: add_note して raise すれば型も連鎖もそのまま。"""

    def annotated() -> None:
        try:
            load("x")
        except ConfigError as err:
            err.add_note("while starting up")
            raise

    with pytest.raises(ConfigError) as info:
        annotated()
    assert info.value.__notes__ == ["while starting up"]
    assert isinstance(info.value.__cause__, ValueError)
