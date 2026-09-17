"""string-pad: str.center / ljust / rjust の Contract を検証する。"""

import pytest


def test_center_pads_both_sides() -> None:
    """左右に埋めて指定幅にする。既定の埋め文字は半角スペース。"""
    assert "abc".center(8) == "  abc   "
    assert "abc".center(8, "*") == "**abc***"
    assert "abc".center(7, "*") == "**abc**"


def test_input_is_not_mutated() -> None:
    """元の文字列は変わらない（新しい文字列を返す）。"""
    s = "abc"
    result = s.center(8)
    assert s == "abc"
    assert result is not s


def test_odd_remainder_side_depends_on_width_parity() -> None:
    """余りが奇数のとき、幅が偶数なら右、奇数なら左に 1 文字多く付く。"""
    assert "abc".center(4) == "abc "
    assert "a".center(4) == " a  "
    assert "ab".center(5) == "  ab "
    assert "abcd".center(7) == "  abcd "


def test_fstring_center_always_leans_right() -> None:
    """f-string の ^ 指定は余りを常に右に寄せるので、幅が奇数のとき str.center と食い違う。"""
    assert f"{'ab':^5}" == " ab  "
    assert "ab".center(5) == "  ab "
    assert f"{'abc':^4}" == "abc "
    assert "abc".center(4) == "abc "


def test_width_not_greater_than_length_returns_original() -> None:
    """幅が長さ以下（0・負数を含む）なら元の文字列をそのまま返し、切り詰めない。"""
    assert "abc".center(3) == "abc"
    assert "abc".center(2) == "abc"
    assert "abc".center(0) == "abc"
    assert "abc".center(-1) == "abc"


def test_empty_string_is_filled_entirely() -> None:
    """空文字は埋め文字だけで幅を満たす。"""
    assert "".center(4, "*") == "****"
    assert "".center(4) == "    "


def test_fillchar_must_be_exactly_one_char() -> None:
    """埋め文字は 1 文字ちょうどでなければ TypeError。"""
    with pytest.raises(TypeError):
        "abc".center(8, "ab")
    with pytest.raises(TypeError):
        "abc".center(8, "")


def test_width_must_support_index_protocol() -> None:
    """幅は __index__ を持つ値（int など）。float や str は TypeError。"""

    class Width:
        def __index__(self) -> int:
            return 8

    assert "abc".center(Width()) == "  abc   "
    with pytest.raises(TypeError):
        "abc".center(8.0)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        "abc".center("8")  # type: ignore[arg-type]


def test_length_is_counted_in_code_points() -> None:
    """長さはコードポイントで数える。絵文字・全角は 1、結合文字は 2。"""
    assert "🐶".center(4, "*") == "*🐶**"
    assert "日本".center(6, "*") == "**日本**"
    assert "é".center(4, "*") == "*é*"


def test_ljust_and_rjust_pad_one_side() -> None:
    """ljust は右に、rjust は左にだけ埋める。"""
    assert "abc".ljust(6, "*") == "abc***"
    assert "abc".rjust(6, "*") == "***abc"
    assert "abc".ljust(2) == "abc"
    assert "abc".rjust(2) == "abc"
