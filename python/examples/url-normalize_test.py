"""url-normalize: urlsplit → _replace → urlunsplit のイディオムの Contract を検証する。"""

import posixpath
from urllib.parse import SplitResult, parse_qsl, urlencode, urlparse, urlsplit, urlunsplit

import pytest


def normalize(url: str) -> str:
    """カードの Usage と同じイディオム。"""
    p = urlsplit(url)
    # userinfo（user:password）は大小を区別するのでホスト部分だけ小文字にする
    userinfo, sep, hostport = p.netloc.rpartition("@")
    netloc = (userinfo + sep if sep else "") + hostport.lower()
    return urlunsplit(p._replace(scheme=p.scheme.lower(), netloc=netloc))


def test_lowercases_scheme_and_netloc_only() -> None:
    """スキームと netloc だけ小文字になり、既定ポート・.. ・// ・%7e はそのまま。"""
    assert normalize("HTTPS://Example.COM:443/a/../b/./c?x=1#f") == "https://example.com:443/a/../b/./c?x=1#f"
    assert normalize("https://example.com/a//b") == "https://example.com/a//b"
    assert normalize("https://example.com/%7e") == "https://example.com/%7e"
    assert normalize("https://example.com/a b/é") == "https://example.com/a b/é"
    assert normalize("https://example.com/Path?Q=1") == "https://example.com/Path?Q=1"


def test_netloc_includes_userinfo_and_port() -> None:
    """netloc にはユーザー情報とポートが含まれ、丸ごと小文字化するとパスワードも小文字になる。"""
    p = urlsplit("https://User:Pw@Example.com:8080/P")
    assert p.netloc == "User:Pw@Example.com:8080"
    # userinfo は大小を区別するのでそのまま、ホストだけ小文字になる
    assert normalize("https://User:Pw@Example.com:8080/P") == "https://User:Pw@example.com:8080/P"
    assert p.hostname == "example.com" and p.username == "User" and p.port == 8080
    assert urlsplit("https://example.com:0080/").port == 80
    assert urlsplit("https://example.com/").port is None
    with pytest.raises(ValueError):
        urlsplit("https://x.com:abc/").port


def test_urlunsplit_drops_empty_query_and_fragment() -> None:
    """空の ? # は消え、ホストだけの URL に / は足さず、パス 'a' には / が補われる。"""
    assert normalize("https://example.com/a?#") == "https://example.com/a"
    assert normalize("https://example.com/?") == "https://example.com/"
    assert normalize("https://example.com") == "https://example.com"
    assert urlunsplit(("https", "x.com", "a", "", "")) == "https://x.com/a"
    assert urlsplit("https://x.com/a?q").geturl() == "https://x.com/a?q"


def test_whitespace_and_control_characters() -> None:
    """先頭の空白とタブ・改行は除かれ、末尾の空白は残る。"""
    assert urlsplit(" https://example.com/a ").path == "/a "
    assert urlsplit("https://x.com/a\tb").path == "/ab"
    assert urlsplit("https://x.com/a\nb").path == "/ab"


def test_missing_scheme_is_interpreted_as_path_or_scheme() -> None:
    """// 無しの example.com/x は path、example.com:8080/x は scheme になる。scheme 引数で補える。"""
    assert urlsplit("example.com/x") == SplitResult("", "", "example.com/x", "", "")
    assert urlsplit("example.com:8080/x").scheme == "example.com"
    assert urlsplit("C:\\a").scheme == "c"
    assert urlsplit("//example.com/x", scheme="https").netloc == "example.com"
    assert urlunsplit(urlsplit("//example.com/x", scheme="https")) == "https://example.com/x"


def test_only_invalid_ipv6_raises() -> None:
    """[ ] が不整合な IPv6 だけ ValueError。"""
    with pytest.raises(ValueError):
        urlsplit("https://[::1/")
    assert urlsplit("https://[::1]:80/a").hostname == "::1"
    assert urlsplit("https://exa mple.com/").netloc == "exa mple.com"


def test_replace_returns_new_splitresult() -> None:
    """_replace は新しい SplitResult を返し、元は変わらない。bytes なら SplitResultBytes。"""
    p = urlsplit("https://X.com/a")
    q = p._replace(netloc="x.com")
    assert isinstance(q, SplitResult) and q.netloc == "x.com" and p.netloc == "X.com"
    assert urlsplit(b"https://X.com/a").netloc == b"X.com"


def test_urlparse_splits_params_but_urlsplit_does_not() -> None:
    """urlparse は ;params を path から分け、urlsplit は分けない。"""
    assert urlparse("https://x.com/a;p=1?q").path == "/a"
    assert urlparse("https://x.com/a;p=1?q").params == "p=1"
    assert urlsplit("https://x.com/a;p=1?q").path == "/a;p=1"


def test_alternatives_sort_query_and_normalize_path() -> None:
    """Alternatives: クエリの並べ替えと posixpath.normpath による .. の解決。"""
    p = urlsplit("https://example.com/a/../b/./c/?b=2&a=1&a=0")
    query = urlencode(sorted(parse_qsl(p.query, keep_blank_values=True)))
    assert query == "a=0&a=1&b=2"
    assert posixpath.normpath(p.path) == "/b/c"
    assert urlunsplit(p._replace(path=posixpath.normpath(p.path), query=query)) == "https://example.com/b/c?a=0&a=1&b=2"
