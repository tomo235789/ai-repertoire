"""string-truncate: textwrap.shorten の Contract を検証する。"""

from textwrap import shorten

import pytest

TEXT = "The quick brown fox jumps over the lazy dog"


def test_default_placeholder() -> None:
    """既定の省略記号は ' [...]'。"""
    assert shorten(TEXT, 20) == "The quick [...]"


def test_cuts_at_word_boundary_within_width() -> None:
    """単語境界で切り、省略記号込みで幅以内に収める。"""
    assert shorten(TEXT, 20, placeholder="...") == "The quick brown..."
    assert shorten(TEXT, 20, placeholder="…") == "The quick brown fox…"
    assert len(shorten(TEXT, 20, placeholder="…")) == 20


def test_text_within_width_is_returned_without_placeholder() -> None:
    """幅に収まる文字列は省略記号なしで返す。"""
    assert shorten(TEXT, 100) == TEXT
    assert shorten("abcdefghij", 10, placeholder="...") == "abcdefghij"


def test_whitespace_is_normalized_even_when_it_fits() -> None:
    """連続空白・改行・タブは半角スペース 1 つにまとめ、前後は落とす。収まる場合も同じ。"""
    assert shorten("  hello    world \n foo  ", 100) == "hello world foo"
    assert shorten("a\tb", 10) == "a b"
    assert shorten("  hello    world \n foo  ", 12) == "hello [...]"


def test_placeholder_only_when_first_word_does_not_fit() -> None:
    """先頭の単語すら入らないときは省略記号（先頭空白を除く）だけを返す。"""
    assert shorten("abcdefghijk", 10, placeholder="...") == "..."
    assert shorten(TEXT, 5) == "[...]"
    assert shorten("日本語の文章です", 5, placeholder="…") == "…"


def test_hyphen_is_a_break_point_by_default() -> None:
    """既定ではハイフンも区切りになる。"""
    assert shorten("hello-world foo", 10, placeholder="...") == "hello-..."
    assert shorten("hello-world foo", 8, placeholder="...") == "..."


def test_width_shorter_than_placeholder_raises() -> None:
    """幅が省略記号より短いと ValueError。幅 0 以下も ValueError。"""
    with pytest.raises(ValueError):
        shorten(TEXT, 2, placeholder="...")
    with pytest.raises(ValueError):
        shorten(TEXT, 0)
    with pytest.raises(ValueError):
        shorten(TEXT, -1)


def test_empty_and_blank_input() -> None:
    """空文字・空白のみは空文字を返す。"""
    assert shorten("", 10) == ""
    assert shorten("   ", 10) == ""


def test_is_pure() -> None:
    """同じ入力からは同じ結果が得られ、入力は変わらない。"""
    text = "  a   b  "
    assert shorten(text, 10) == shorten(text, 10)
    assert text == "  a   b  "


def test_slice_alternative_cuts_by_character_count() -> None:
    """Alternatives の文字数スライスは単語境界を無視し、結果は n + 3 文字。"""
    assert TEXT[:10] + "..." == "The quick ..."
    assert len(TEXT[:10] + "...") == 13
