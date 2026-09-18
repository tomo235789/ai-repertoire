"""error-assert-never: typing.assert_never の Contract を検証する。"""

import subprocess
import sys
import textwrap
import typing
from enum import Enum
from typing import Literal, assert_never, cast

import pytest

Kind = Literal["circle", "square"]


def area(kind: Kind, size: float) -> float:
    """カードの Usage と同じ関数。全ケースを処理しているので type: ignore 無しで型検査が通る形。"""
    match kind:
        case "circle":
            return 3.14159 * size**2
        case "square":
            return size**2
        case _:
            assert_never(kind)


class Color(Enum):
    RED = "red"
    BLUE = "blue"


def label(color: Color) -> str:
    if color is Color.RED:
        return "赤"
    elif color is Color.BLUE:
        return "青"
    else:
        assert_never(color)


def test_exhaustive_branches_return_normally() -> None:
    """全ケースを処理していれば普通に値を返す。"""
    assert area("circle", 1.0) == 3.14159
    assert area("square", 2.0) == 4.0
    assert label(Color.RED) == "赤"


def test_unreachable_value_raises_assertion_error_at_runtime() -> None:
    """型を通らない値が届くと AssertionError で、メッセージに repr が入る。"""
    with pytest.raises(AssertionError) as info:
        area(cast(Kind, "triangle"), 1.0)
    assert str(info.value) == "Expected code to be unreachable, but got: 'triangle'"
    with pytest.raises(AssertionError):
        label(cast(Color, "green"))


def test_repr_is_truncated_to_100_chars() -> None:
    """メッセージの repr は 100 文字で切られ、末尾に ... が付く。"""
    with pytest.raises(AssertionError) as info:
        assert_never(cast(typing.Never, "x" * 200))
    message = str(info.value)
    assert message.endswith("...")
    assert len(message) == len("Expected code to be unreachable, but got: ") + 100 + 3


def test_signature_is_never_to_never() -> None:
    """引数と戻り値の型注釈は Never。"""
    hints = typing.get_type_hints(assert_never)
    assert hints["arg"] is typing.Never
    assert hints["return"] is typing.Never


def test_not_removed_by_optimize_flag() -> None:
    """raise 文なので python -O でも消えない。"""
    code = textwrap.dedent(
        """
        from typing import assert_never
        try:
            assert_never("x")
        except AssertionError as e:
            print("raised:", e)
        else:
            print("no raise")
        """
    )
    result = subprocess.run([sys.executable, "-O", "-c", code], capture_output=True, text=True, check=True)
    assert result.stdout.strip() == "raised: Expected code to be unreachable, but got: 'x'"


def test_missing_case_is_not_detected_at_runtime() -> None:
    """Pitfalls: 網羅漏れは実行しても検出されない。漏れたケースは実行時に AssertionError になるだけ。"""

    def incomplete(kind: Kind) -> str:
        match kind:
            case "circle":
                return "c"
            case _:
                assert_never(kind)  # 型検査器なら "square" が Never に代入できずエラーになる行

    assert incomplete("circle") == "c"
    with pytest.raises(AssertionError):
        incomplete("square")
