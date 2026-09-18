---
id: url-join-path
lang: python
title: URL にパスを結合する
tags: [URL結合, 相対URL, ベースURL, エンドポイント, join-url, resolve-url, base-url, relative-url]
lib: stdlib
fn: urllib.parse.urljoin
since: "3.0"
verified: 2026-09-17
status: public
---

ベース URL に相対パスを解決して絶対 URL を作る。API のエンドポイントやリンク先を組み立てるときに文字列連結の代わりに使う。

## Signature

```python
urllib.parse.urljoin(base, url, allow_fragments=True)
```

## Usage

```python
from urllib.parse import urljoin

base = "https://api.example.com/v1/"
urljoin(base, "users")               # => 'https://api.example.com/v1/users'
urljoin("https://api.example.com/v1", "users")  # => 'https://api.example.com/users'（末尾 / が無いと v1 が置き換わる）
urljoin(base, "/health")             # => 'https://api.example.com/health'（先頭 / はホスト直下）
urljoin(base, "../v2/users")         # => 'https://api.example.com/v2/users'
urljoin(base, "users?page=2")        # => 'https://api.example.com/v1/users?page=2'
```

## Contract

- `url` を `base` に対する相対参照として解決する（RFC 3986）。`base` のパスの最後のセグメント（末尾 `/` の後ろ、無ければファイル名相当）が置き換わる
- `url` が `/` で始まればホスト直下、`//host/...` ならスキームだけ引き継いで別ホスト、スキーム付きなら `base` を無視して `url` をそのまま返す（`mailto:x@y` や `javascript:...` も。大文字も保つ）
- `..` は 1 つ上へ戻り、ルートより上には戻れない（`'https://x.com/a/b/c'` + `'../../../../d'` → `'https://x.com/d'`）。`.` は現在の位置。`url` 内の `//` は 1 つに畳まれる（`'b//c'` → `'b/c'`）
- **`base` のクエリとフラグメントは引き継がない**: `url` にパスがあれば捨てる。`url` が `?r=2` だけならパスを保ってクエリを置き換え、`#g` だけならクエリも保つ。`url` が `''` なら `base` をそのまま返す（フラグメントも残る）
- パーセントエンコードはしない（`'c d/é'` はそのまま結合される）
- 例外を投げない。`base` が `''` なら `url` をそのまま返し、`base` にスキームが無くても文字列として解決する（`'v1/'` + `'users'` → `'v1/users'`）。`mailto:a@b` のような階層を持たないスキームの `base` に相対パスを足すと `url` がそのまま返る（`'x'`）
- `base` のスキームは小文字化されるがホストはされない（`'HTTPS://X.com/a/'` + `'b'` → `'https://X.com/a/b'`）
- `str` 同士か `bytes` 同士。混ぜると `TypeError`

## Alternatives

- 文字列連結 `base + path` は `//` の重複や `/` の欠落を起こし、`..` も解決しない
- クエリは `urlencode`（url-build-query）で作り、`urlsplit(url)._replace(query=...)` → `urlunsplit` で差し替える
- ファイルパスは `pathlib`（io-join-path）。絶対パスと `..` の規則が違う
- WHATWG 準拠の解決（エンコードや正規化込み）が要るなら `yarl` の `URL.join` や `hyperlink`

## Pitfalls

- TypeScript（Node）の `new URL(path, base)` と同じ RFC 3986 の解決規則だが、`urljoin` は不正でも例外を投げず（`mailto:` ベースで `'x'` が返る）、空白や非 ASCII をエンコードしない。結果を `urlsplit` して `netloc` があるか確かめる
- ベースの末尾 `/` の有無で結果が変わる。ディレクトリのつもりのベースは末尾を `/` で終える
- 先頭 `/` の相対パスはベースのパスを全部捨てる。プレフィックス付きで配備される API では `'/users'` ではなく `'users'` を渡す
- ユーザー入力を `url` に渡すと `'javascript:alert(1)'` や `'//evil.com/'` でホストごと乗っ取れる。結合後にスキームとホストを検証する
- `base` のフラグメントは `url=''` のときだけ残る。Node は `''` でもフラグメントを落とす

## Test

`examples/url-join-path_test.py`
