"""error-custom-class: Exception のサブクラス定義の Contract を検証する。"""

import copy
import json
import pickle
import traceback

import pytest


class AppError(Exception):
    """アプリ内の例外の基底。"""


class NotFoundError(AppError):
    def __init__(self, key: str) -> None:
        super().__init__(key)
        self.key = key

    def __str__(self) -> str:
        return f"not found: {self.key}"


class MessageOnlyError(AppError):
    """Pitfalls: メッセージだけ args に渡す壊れた例。"""

    def __init__(self, key: str) -> None:
        super().__init__(f"not found: {key}")
        self.key = key


class TwoArgsError(AppError):
    """Pitfalls: __init__ の引数の数と args が合わない例（pickle はモジュール直下のクラスしか扱えない）。"""

    def __init__(self, key: str, extra: int) -> None:
        super().__init__(key)
        self.key = key


def test_args_str_and_repr() -> None:
    """args はコンストラクタ引数のタプル。str は __str__、repr は 型名(*args)。"""
    err = NotFoundError("user:1")
    assert err.args == ("user:1",)
    assert err.key == "user:1"
    assert str(err) == "not found: user:1"
    assert repr(err) == "NotFoundError('user:1')"


def test_default_str_depends_on_number_of_args() -> None:
    """__str__ を上書きしなければ args が 0 個なら ''、1 個ならその str、2 個以上ならタプルの str。"""
    assert str(AppError()) == ""
    assert str(AppError("a")) == "a"
    assert str(AppError("a", 1)) == "('a', 1)"


def test_traceback_last_line_uses_class_name_and_str() -> None:
    """traceback の最終行は 型名: str(e)（__main__ 以外のモジュールでは モジュール名.型名）。クラス名は自動で使われる。"""
    err = NotFoundError("user:1")
    assert traceback.format_exception_only(err) == [f"{__name__}.NotFoundError: not found: user:1\n"]
    assert traceback.format_exception_only(ValueError("v")) == ["ValueError: v\n"]


def test_except_catches_subclasses_in_order() -> None:
    """except AppError はサブクラスも捕捉し、先に書いた具体的な except が優先される。"""
    seen: list[str] = []
    for exc in (NotFoundError("k"), AppError("base")):
        try:
            raise exc
        except NotFoundError as err:
            seen.append(f"specific:{err.key}")
        except AppError:
            seen.append("base")
    assert seen == ["specific:k", "base"]
    assert isinstance(NotFoundError("k"), AppError)


def test_pickle_round_trip_requires_args_to_match_init() -> None:
    """pickle は type(e)(*e.args) で作り直す。引数を args に残していれば復元できる。"""
    restored = pickle.loads(pickle.dumps(NotFoundError("user:1")))
    assert isinstance(restored, NotFoundError)
    assert restored.key == "user:1"
    assert str(restored) == "not found: user:1"
    assert copy.copy(NotFoundError("user:1")).key == "user:1"


def test_message_only_args_breaks_pickle() -> None:
    """Pitfalls: メッセージだけ渡すと復元後の args / str がメッセージの二重になる。引数の数が違えば TypeError。"""
    broken = pickle.loads(pickle.dumps(MessageOnlyError("user:1")))
    assert broken.key == "user:1"  # __dict__ は復元される
    assert broken.args == ("not found: not found: user:1",)
    assert str(broken) == "not found: not found: user:1"
    with pytest.raises(TypeError):
        pickle.loads(pickle.dumps(TwoArgsError("k", 1)))


def test_args_are_set_even_without_calling_super_init() -> None:
    """super().__init__() を呼ばなくても args はコンストラクタ引数から設定される。"""

    class NoSuperError(Exception):
        def __init__(self, key: str) -> None:
            self.key = key

    err = NoSuperError("k")
    assert err.args == ("k",)
    assert str(err) == "k"


def test_raising_class_without_required_args_is_type_error() -> None:
    """引数が必須の例外をクラスだけで raise すると TypeError。"""
    with pytest.raises(TypeError):
        raise NotFoundError  # type: ignore[call-arg]


def test_add_note_appends_to_notes_and_traceback() -> None:
    """add_note で文脈を足すと __notes__ に溜まり、traceback の出力に現れる。"""
    err = NotFoundError("user:1")
    err.add_note("while loading config")
    assert err.__notes__ == ["while loading config"]
    assert traceback.format_exception_only(err) == [f"{__name__}.NotFoundError: not found: user:1\n", "while loading config\n"]


def test_json_dumps_fails_and_equality_is_identity() -> None:
    """Pitfalls: json.dumps は TypeError。== は同一性で、同じ内容でも別インスタンスは等しくない。"""
    with pytest.raises(TypeError):
        json.dumps(NotFoundError("k"))
    assert NotFoundError("a") != NotFoundError("a")
    err = NotFoundError("a")
    assert err == err
