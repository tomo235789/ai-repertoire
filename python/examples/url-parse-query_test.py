"""url-parse-query: urllib.parse.parse_qs / parse_qsl の Contract を検証する。"""

from urllib.parse import parse_qs, parse_qsl, unquote, unquote_plus, urlsplit

import pytest

QS = "q=foo+bar&tag=a&tag=b&page=2&empty=&flag"


def test_values_are_lists_in_first_seen_order() -> None:
    """parse_qs は常にリスト。キーは最初に出現した順。parse_qsl は組のリストで出現順。"""
    assert parse_qs(QS) == {"q": ["foo bar"], "tag": ["a", "b"], "page": ["2"]}
    assert parse_qs(QS)["page"] == ["2"]
    assert list(parse_qs("b=1&a=2&b=3")) == ["b", "a"]
    assert parse_qsl(QS) == [("q", "foo bar"), ("tag", "a"), ("tag", "b"), ("page", "2")]
    assert dict(parse_qsl(QS)) == {"q": "foo bar", "tag": "b", "page": "2"}


def test_values_are_strings() -> None:
    """値は常に str で、数値には変換されない。無いキーは KeyError / get で None。"""
    assert parse_qs("n=42&t=true") == {"n": ["42"], "t": ["true"]}
    assert parse_qs("a=1").get("missing") is None
    with pytest.raises(KeyError):
        parse_qs("a=1")["missing"]


def test_decoding_rules() -> None:
    """+ と %20 は空白、%XX は UTF-8 でデコード。キーも同様。不正な % はそのまま、不正 UTF-8 は U+FFFD。"""
    assert parse_qs("a=%20x%2Bb&u=%E6%97%A5") == {"a": [" x+b"], "u": ["日"]}
    assert parse_qsl("a+b=c+d") == [("a b", "c d")]
    assert parse_qs("a=%zz&b=%") == {"a": ["%zz"], "b": ["%"]}
    assert parse_qs("a=%FF") == {"a": ["\ufffd"]}
    with pytest.raises(UnicodeDecodeError):
        parse_qs("a=%FF", errors="strict")
    assert parse_qs("u=%93%FA", encoding="cp932") == {"u": ["日"]}


def test_blank_values_and_strict_parsing() -> None:
    """空値は既定で捨てる。keep_blank_values=True で残す。strict_parsing は = 無しと空フィールドで ValueError。"""
    assert parse_qs(QS, keep_blank_values=True)["empty"] == [""]
    assert parse_qs(QS, keep_blank_values=True)["flag"] == [""]
    assert parse_qsl("empty=&flag", keep_blank_values=True) == [("empty", ""), ("flag", "")]
    with pytest.raises(ValueError):
        parse_qs("a=1&b", strict_parsing=True)
    with pytest.raises(ValueError):
        parse_qs("a=1&&b=2", strict_parsing=True)
    assert parse_qs("a=1&b=", strict_parsing=True) == {"a": ["1"]}


def test_separator_is_ampersand_only() -> None:
    """; は区切りにならない（separator で変更可）。a=b=c は最初の = で分ける。"""
    assert parse_qs("a=1;b=2") == {"a": ["1;b=2"]}
    assert parse_qs("a=1;b=2", separator=";") == {"a": ["1"], "b": ["2"]}
    assert parse_qs("a=b=c") == {"a": ["b=c"]}


def test_leading_question_and_fragment_are_not_stripped() -> None:
    """先頭の ? も #f も取り除かない。URL 全体は urlsplit().query で取り出す。"""
    assert parse_qs("?a=1") == {"?a": ["1"]}
    assert parse_qs("a=1#f") == {"a": ["1#f"]}
    assert parse_qs("https://x.com/p?a=1") == {"https://x.com/p?a": ["1"]}
    assert parse_qs(urlsplit("https://x.com/p?a=1&a=2#f").query) == {"a": ["1", "2"]}


def test_max_num_fields() -> None:
    """max_num_fields を超えると ValueError。"""
    assert parse_qs("a=1&b=2", max_num_fields=2) == {"a": ["1"], "b": ["2"]}
    with pytest.raises(ValueError):
        parse_qs("a=1&b=2&c=3", max_num_fields=2)


def test_empty_and_bytes_input() -> None:
    """空文字列は {} / []。bytes を渡せばキーと値も bytes。"""
    assert parse_qs("") == {}
    assert parse_qsl("") == []
    assert parse_qs(b"a=1&b=x+y") == {b"a": [b"1"], b"b": [b"x y"]}


def test_unquote_alternatives() -> None:
    """Alternatives: unquote_plus は + も空白に、unquote は + をそのまま。不正な % で例外にならない。"""
    assert unquote_plus("a+b%20c") == "a b c"
    assert unquote("a+b%20c") == "a+b c"
    assert unquote("%zz") == "%zz"


def test_single_value_access_patterns() -> None:
    """Pitfalls: [0] で取り出す。無いキーは get の既定値か dict(parse_qsl()) で扱う。"""
    d = parse_qs(QS)
    assert d["q"][0] == "foo bar"
    assert d.get("missing", [""])[0] == ""
    assert dict(parse_qsl(QS)).get("missing") is None
