"""url-is-absolute: urlparse(s).scheme and .netloc による判定の Contract を検証する。"""

from urllib.parse import urlparse

import pytest


def is_absolute_url(s: str) -> bool:
    """カードの Usage と同じイディオム。"""
    p = urlparse(s)
    return bool(p.scheme and p.netloc)


def test_true_for_scheme_with_netloc() -> None:
    """スキームと netloc の両方があれば True。スキームは小文字化される。"""
    for s in ("https://example.com/a", "ftp://x", "s3://bucket/key", "file://host/a", "a+b.c://x", "ws://x", "http://x?q"):
        assert is_absolute_url(s), s
    assert urlparse("HTTPS://EXAMPLE.COM").scheme == "https"
    assert urlparse("HTTPS://EXAMPLE.COM").netloc == "EXAMPLE.COM"


def test_false_without_scheme() -> None:
    """スキームが無い・スキーム相対・空文字列は False。scheme 引数で補える。"""
    for s in ("example.com/a", "/a/b", "//cdn.example.com/x.js", "", "  "):
        assert not is_absolute_url(s), s
    assert urlparse("//cdn.example.com/x.js").netloc == "cdn.example.com"
    p = urlparse("//cdn.example.com/x.js", scheme="https")
    assert bool(p.scheme and p.netloc)


def test_false_without_netloc() -> None:
    """mailto: や data: のように netloc が無いスキームは False。"""
    for s in ("mailto:a@b", "data:,x", "javascript:alert(1)", "file:///a", "http:example.com", "http:/example.com", "http://"):
        assert not is_absolute_url(s), s
    assert urlparse("mailto:a@b").scheme == "mailto"
    assert urlparse("mailto:a@b").netloc == ""


def test_windows_drive_and_host_port_look_like_scheme() -> None:
    """c:\\a や localhost:8080 は scheme に見えるが netloc が無いので False。数字始まりはスキームにならない。"""
    assert urlparse("c:\\a").scheme == "c"
    assert urlparse("C:/Users/x").scheme == "c"
    assert urlparse("localhost:8080").scheme == "localhost"
    assert urlparse("example.com:443").scheme == "example.com"
    for s in ("c:\\a", "C:/Users/x", "localhost:8080", "example.com:443"):
        assert not is_absolute_url(s), s
    assert urlparse("1abc://x").scheme == ""


def test_netloc_is_not_validated() -> None:
    """netloc の中身は検証しない。port を触ったときだけ ValueError。"""
    for s in ("http://user@", "http://:80", "http://x.com:abc", "https:// example.com"):
        assert is_absolute_url(s), s
    with pytest.raises(ValueError):
        urlparse("http://x.com:abc").port


def test_whitespace_handling() -> None:
    """先頭の空白とタブ・改行は除かれる。末尾の空白は netloc に残る。"""
    assert is_absolute_url("\t https://x.com")
    assert is_absolute_url("https://x.com\n")
    assert urlparse("https://x\t.com/a").netloc == "x.com"
    assert urlparse(" https://example.com ").netloc == "example.com "


def test_only_invalid_ipv6_raises() -> None:
    """[ ] が不整合な IPv6 だけ ValueError。bytes も受ける。"""
    with pytest.raises(ValueError):
        is_absolute_url("https://[::1/")
    assert urlparse("https://[::1]:8080/a").hostname == "::1"
    p = urlparse(b"https://x.com")
    assert bool(p.scheme and p.netloc)


def test_http_only_variant() -> None:
    """Alternatives: http(s) だけを許可する判定。"""

    def is_http_url(s: str) -> bool:
        p = urlparse(s)
        return p.scheme in ("http", "https") and bool(p.netloc)

    assert is_http_url("https://example.com")
    assert not is_http_url("ftp://example.com")
    assert not is_http_url("javascript:alert(1)")
