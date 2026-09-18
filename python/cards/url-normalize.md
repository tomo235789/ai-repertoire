---
id: url-normalize
lang: python
title: URL を正規化する
tags: [URL正規化, 同一判定, 重複排除, 標準形, normalize-url, canonical, dedupe-url, url-equality]
lib: stdlib
fn: urllib.parse.urlsplit
since: "3.0"
verified: 2026-09-17
status: public
---

`urlsplit` で分解し、スキームとホストを小文字にして `urlunsplit` で組み直す。stdlib に完全な正規化関数は無く、このイディオムが行うのはその分だけ。同じ URL かの比較やキャッシュキーに使う。

## Signature

```python
urllib.parse.urlsplit(urlstring, scheme='', allow_fragments=True)  # -> SplitResult。_replace() → urlunsplit() で組み直す
```

## Usage

```python
from urllib.parse import urlsplit, urlunsplit

def normalize(url: str) -> str:
    p = urlsplit(url)
    user, sep, host = p.netloc.rpartition("@")  # userinfo は大小を区別するので触らない
    return urlunsplit(p._replace(scheme=p.scheme.lower(), netloc=user + sep + host.lower()))

normalize("HTTPS://Example.COM:443/a/../b/./c?x=1#f")
# => 'https://example.com:443/a/../b/./c?x=1#f'（スキームとホストだけ小文字。ポートとパスはそのまま）
normalize("https://example.com/a?#")  # => 'https://example.com/a'（空のクエリ・フラグメントは消える）
```

## Contract

- stdlib に URL 正規化関数は無い。上のイディオムがやるのは **スキームと netloc の小文字化と、空のクエリ・フラグメントの除去だけ**
- `urlsplit` は構文で分けるだけで値を変えない: 既定ポート `:443`、`/a/../b/./c`、`//` の重複、`%7e`、パスの空白や非 ASCII はすべてそのまま
- `netloc` にはユーザー情報とポートが含まれる（`'User:Pw@Example.com:8080'`）。丸ごと小文字化するとパスワードも小文字になる。`p.hostname` は常に小文字（`'example.com'`）、`p.port` は `int`（`'0080'` → `80`）か `None` で、数字でなければ触った時点で `ValueError`
- `urlunsplit` は空のクエリ・フラグメントの `?` `#` を落とし（`'https://x.com/a?#'` → `'https://x.com/a'`）、ホストだけの URL に末尾 `/` は足さない（`'https://example.com'` はそのまま）。`netloc` があってパスが `'a'` なら `/` を補う
- 先頭の空白と、どこにあってもタブ・改行は除いてから解析する（`'https://x.com/a\tb'` → path `/ab`）。末尾の空白は残る
- `//` 無しの `'example.com/x'` は全部 path（`netloc=''`）。`'example.com:8080/x'` は **scheme が `'example.com'`** になる。`'C:\a'` は scheme `'c'`。`scheme="https"` 引数で `'//example.com/x'` に既定スキームを補える
- `[` `]` が不整合な IPv6（`'https://[::1/'`）は `ValueError`。それ以外の文字列で例外は出ない
- `_replace` は `namedtuple` の API で新しい `SplitResult` を返す。`p.geturl()` は `urlunsplit(p)` と同じ。`bytes` を渡せば `SplitResultBytes`

## Alternatives

- 比較だけなら `normalize(a) == normalize(b)`
- クエリの順序も揃えるなら `query=urlencode(sorted(parse_qsl(p.query, keep_blank_values=True)))` を `_replace` に足す
- パスの `.` `..` は `posixpath.normpath(p.path)` で畳める（`'/a/../b/./c'` → `'/b/c'`。末尾の `/` は落ちる）。既定ポートは `p.port in (80, 443)` を見て `hostname` から `netloc` を組み直す
- IDNA・パーセントエンコードの正規化・既定ポート除去まで含む WHATWG 相当の正規化は `yarl`、`hyperlink`、`url-normalize` パッケージ
- `;params` を `path` から分けたいときだけ `urlparse`。往復させるなら `urlsplit`

## Pitfalls

- TypeScript（Node）の `new URL(s).href` はホスト小文字化・既定ポート除去・`..` 解決・空白のエンコードまでやるが、`urlsplit` はどれもしない。同じ URL でも両言語で文字列が一致しない
- `'example.com/x'` はホストではなくパスと解釈される。スキーム無しの入力は先に `'//'` か `'https://'` を補う
- `netloc.lower()` はパスワードも小文字にする。ユーザー情報付き URL は `username` / `password` / `hostname` / `port` から組み直す
- `urlunsplit(urlsplit(s))` は元の文字列と一致しないことがある（空の `?` `#` が消える、`'a'` に `/` が付く）。往復の同一性を前提にしない

## Test

`examples/url-normalize_test.py`
