"""url-join-path: urllib.parse.urljoin の Contract を検証する。"""

from urllib.parse import urljoin, urlsplit

import pytest

BASE = "https://api.example.com/v1/"


def test_resolves_relative_reference() -> None:
    """ベースの最後のセグメントが置き換わる。末尾 / の有無で結果が変わる。"""
    assert urljoin(BASE, "users") == "https://api.example.com/v1/users"
    assert urljoin("https://api.example.com/v1", "users") == "https://api.example.com/users"
    assert urljoin(BASE, "./users") == "https://api.example.com/v1/users"
    assert urljoin(BASE, "users/") == "https://api.example.com/v1/users/"


def test_leading_slash_scheme_relative_and_absolute() -> None:
    """先頭 / はホスト直下、//host はスキームだけ引き継ぐ、スキーム付きはそのまま。"""
    assert urljoin(BASE, "/health") == "https://api.example.com/health"
    assert urljoin(BASE, "//cdn.example.com/x.js") == "https://cdn.example.com/x.js"
    assert urljoin(BASE, "http://other.com/a") == "http://other.com/a"
    assert urljoin(BASE, "HTTP://Other.com/A") == "HTTP://Other.com/A"
    assert urljoin(BASE, "mailto:x@y") == "mailto:x@y"


def test_dotdot_and_double_slash() -> None:
    """.. は 1 つ上へ戻り、ルートより上には戻れない。// は 1 つに畳まれる。"""
    assert urljoin(BASE, "../v2/users") == "https://api.example.com/v2/users"
    assert urljoin(BASE, "..") == "https://api.example.com/"
    assert urljoin("https://x.com/a/b/c", "../../d") == "https://x.com/d"
    assert urljoin("https://x.com/a/b/c", "../../../../d") == "https://x.com/d"
    assert urljoin("https://x.com/a/", "b//c") == "https://x.com/a/b/c"


def test_query_and_fragment_of_base_are_not_inherited() -> None:
    """ベースのクエリ・フラグメントはパスがあれば捨てる。? だけならパスを保ち、# だけならクエリも保つ。"""
    base = "https://x.com/a?q=1#f"
    assert urljoin(base, "b") == "https://x.com/b"
    assert urljoin(base, "?r=2") == "https://x.com/a?r=2"
    assert urljoin(base, "#g") == "https://x.com/a?q=1#g"
    assert urljoin(base, "") == base
    assert urljoin(BASE, "users?page=2") == "https://api.example.com/v1/users?page=2"


def test_does_not_percent_encode() -> None:
    """空白や非 ASCII はエンコードされない。"""
    assert urljoin(BASE, "c d/é") == "https://api.example.com/v1/c d/é"


def test_never_raises_on_odd_inputs() -> None:
    """空のベース・スキーム無しのベース・階層を持たないスキームでも例外を投げない。"""
    assert urljoin("", "users") == "users"
    assert urljoin("v1/", "users") == "v1/users"
    assert urljoin("mailto:a@b", "x") == "x"
    assert urlsplit(urljoin("mailto:a@b", "x")).netloc == ""


def test_scheme_is_lowercased_but_host_is_not() -> None:
    """ベースのスキームは小文字化されるがホストはそのまま。"""
    assert urljoin("HTTPS://X.com/a/", "b") == "https://X.com/a/b"


def test_str_and_bytes_cannot_be_mixed() -> None:
    """str 同士か bytes 同士。混ぜると TypeError。"""
    assert urljoin(b"https://x.com/a/", b"b") == b"https://x.com/a/b"
    with pytest.raises(TypeError):
        urljoin("https://x.com/a/", b"b")  # type: ignore[arg-type]


def test_user_input_can_hijack_host() -> None:
    """Pitfalls: ユーザー入力でスキームやホストを乗っ取れる。結合後に検証する。"""
    for bad in ("javascript:alert(1)", "//evil.com/"):
        joined = urljoin(BASE, bad)
        assert urlsplit(joined).netloc != "api.example.com"
