---
id: url-is-absolute
lang: python
title: URL が絶対か判定する
tags: [URL判定, 絶対URL, 妥当性検証, スキーム, is-absolute-url, validate-url, can-parse, url-check]
lib: stdlib
fn: urllib.parse.urlparse
since: "3.0"
verified: 2026-09-17
status: public
---

`urlparse` の結果に scheme と netloc の両方があるかで、スキーム付きの絶対 URL かを判定する。入力値の検証や、相対パスと絶対 URL で処理を分けるときに使う。

## Signature

```python
urllib.parse.urlparse(urlstring, scheme='', allow_fragments=True)  # bool(p.scheme and p.netloc) で判定
```

## Usage

```python
from urllib.parse import urlparse

def is_absolute_url(s: str) -> bool:
    p = urlparse(s)
    return bool(p.scheme and p.netloc)

is_absolute_url("https://example.com/a")   # => True
is_absolute_url("example.com/a")           # => False（スキームが無い）
is_absolute_url("//cdn.example.com/x.js")  # => False（スキーム相対）
is_absolute_url("mailto:a@b")              # => False（netloc が無い）
```

## Contract

- `scheme` は英字で始まり英数と `+` `-` `.` が続く `:` の前の部分で、小文字化される。`netloc` は `//` の直後から次の `/` `?` `#` まで
- `https://example.com/a`、`ftp://x`、`s3://bucket/key`、`file://host/a`、`a+b.c://x` は `True`。`example.com/a`、`/a/b`、`''` は `False`
- スキーム相対 `//host/path` は `scheme=''` で `False`。`urlparse(s, scheme="https")` で既定スキームを補える
- `mailto:a@b`、`data:,x`、`javascript:alert(1)`、`file:///a`、`http:example.com`、`http://` は `netloc` が空で `False`
- `c:\a` / `C:/Users/x` は `scheme='c'`、`netloc=''` で `False`。`localhost:8080` / `example.com:443` も `scheme='localhost'` / `'example.com'` で `False`（`1abc://x` は数字始まりなのでスキームにならない）
- `netloc` の中身は検証しない: `http://user@`、`http://:80`、`http://x.com:abc`、`https:// example.com`（空白入り）は `True`。`p.port` を触ったときだけ `ValueError`
- 先頭の空白と、どこにあってもタブ・改行は除いてから解析する（`'\t https://x.com'` は `True`）。末尾の空白は `netloc` に残る
- 例外は `[` `]` が不整合な IPv6（`'https://[::1/'`）のときだけ `ValueError`。それ以外の文字列では投げない。`bytes` も受ける

## Alternatives

- `http(s)` だけ許可するなら `p.scheme in ("http", "https") and bool(p.netloc)`
- 相対 URL を絶対にするなら `urljoin(base, s)`（url-join-path）
- ホスト名の形式まで検証するなら `validators.url` や `pydantic.AnyUrl`。`urlparse` は構文で分割するだけで妥当性は見ない
- `;params` が要らなければ `urlsplit` でも同じ判定ができる

## Pitfalls

- TypeScript（Node）の `URL.canParse` は `mailto:` や `c:\a` を `true` にするが、このイディオムは `netloc` を要求するので `False`。逆に `http://user@` や `https:// example.com` は `canParse` が `false` でも `True` になる。ホスト名の妥当性は別に確認する
- `urlparse(s).scheme != ""` だけで判定すると Windows のパス `C:\...` や `localhost:8080` を絶対 URL と誤判定する。`netloc` も見る
- 前後の空白は `strip()` してから渡す（末尾の空白は `netloc` に残って `True` になる）
- `[` を含む入力で `ValueError` が出る。外部入力なら `try/except ValueError` で包む

## Test

`examples/url-is-absolute_test.py`
