"""url-build-query: urllib.parse.urlencode の Contract を検証する。"""

from urllib.parse import parse_qsl, quote, quote_plus, urlencode

import pytest


def test_builds_key_value_pairs_in_insertion_order() -> None:
    """key=value を & でつなぐ。先頭に ? は無く、順序は挿入順。空なら ''。"""
    assert urlencode({"q": "foo bar", "page": 2}) == "q=foo+bar&page=2"
    assert urlencode({"z": 1, "a": 2}) == "z=1&a=2"
    assert urlencode([("tag", "a"), ("tag", "b")]) == "tag=a&tag=b"
    assert urlencode({}) == ""
    assert urlencode({"a": "", "b": "x"}) == "a=&b=x"


def test_quote_plus_encoding_rules() -> None:
    """空白は +、+ は %2B、& = / ? # と非 ASCII はパーセントエンコード。_.-~ と英数字はそのまま。"""
    assert urlencode({"q": "a&b=c", "s": "a/b?c#d", "p": "+"}) == "q=a%26b%3Dc&s=a%2Fb%3Fc%23d&p=%2B"
    assert urlencode({"u": "日本"}) == "u=%E6%97%A5%E6%9C%AC"
    assert urlencode({"k": "Az09_.-~"}) == "k=Az09_.-~"
    assert urlencode({"k": "*!'()"}) == "k=%2A%21%27%28%29"
    assert urlencode({"a b": "1", "c&": 2}) == "a+b=1&c%26=2"


def test_quote_via_and_safe() -> None:
    """quote_via=quote で空白が %20。safe でエンコードしない文字を増やせる。"""
    assert urlencode({"q": "foo bar", "p": "a+b"}, quote_via=quote) == "q=foo%20bar&p=a%2Bb"
    assert urlencode({"path": "a/b", "s": "a b"}, safe="/") == "path=a/b&s=a+b"
    assert quote_plus("a b+c") == "a+b%2Bc"
    assert quote("a b+c") == "a%20b%2Bc"


def test_values_are_stringified() -> None:
    """値は str() される。None は 'None'、True は 'True'。bytes はそのままエンコード。"""
    assert urlencode({"a": None, "b": True, "c": 1.5, "d": b"x y"}) == "a=None&b=True&c=1.5&d=x+y"
    assert urlencode({k: v for k, v in {"a": None, "b": 1}.items() if v is not None}) == "b=1"


def test_doseq_for_multiple_values() -> None:
    """doseq=False ではリストの repr がエンコードされ、doseq=True で要素ごとに展開。空リストは消える。"""
    assert urlencode({"tag": ["a", "b"]}) == "tag=%5B%27a%27%2C+%27b%27%5D"
    assert urlencode({"tag": ["a", "b"], "q": "x"}, doseq=True) == "tag=a&tag=b&q=x"
    assert urlencode({"tag": ("a", "b")}, doseq=True) == "tag=a&tag=b"
    assert urlencode({"tag": [], "q": "x"}, doseq=True) == "q=x"


def test_doseq_keeps_scalar_values_whole() -> None:
    """doseq=True でも str / bytes / int は 1 つの値（文字ごとに分解しない）。"""
    assert urlencode({"q": "ab", "b": b"cd", "n": 12}, doseq=True) == "q=ab&b=cd&n=12"


def test_encoding_argument() -> None:
    """encoding で非 ASCII のエンコード方式を変えられる。"""
    assert urlencode({"u": "日本"}, encoding="shift_jis") == "u=%93%FA%96%7B"


def test_invalid_input_raises_type_error() -> None:
    """辞書でも組の列でもない入力は TypeError。"""
    with pytest.raises(TypeError):
        urlencode("a=1")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        urlencode(["a"])  # type: ignore[list-item]


def test_roundtrip_with_parse_qsl() -> None:
    """parse_qsl の結果をそのまま戻せる。"""
    qs = "a=1&a=2&b=x+y"
    assert urlencode(parse_qsl(qs)) == qs
