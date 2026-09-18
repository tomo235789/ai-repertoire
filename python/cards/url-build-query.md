---
id: url-build-query
lang: python
title: クエリ文字列を組み立てる
tags: [クエリ文字列, URLエンコード, 検索パラメータ, GETパラメータ, query-string, url-encode, search-params, build-query]
lib: stdlib
fn: urllib.parse.urlencode
since: "3.0"
verified: 2026-09-17
status: public
---

キーと値の組から `a=1&b=x+y` の形のクエリ文字列を、エンコード込みで作る。API 呼び出しの URL やリンクの組み立てに使う。

## Signature

```python
urllib.parse.urlencode(query, doseq=False, safe='', encoding=None, errors=None, quote_via=quote_plus)
```

## Usage

```python
from urllib.parse import quote, urlencode

urlencode({"q": "foo bar", "page": 2})       # => 'q=foo+bar&page=2'
urlencode({"tag": ["a", "b"]}, doseq=True)   # => 'tag=a&tag=b'（同じキーを複数）
urlencode([("tag", "a"), ("tag", "b")])      # => 'tag=a&tag=b'（組のリストでも可）
urlencode({"q": "foo bar"}, quote_via=quote)  # => 'q=foo%20bar'
urlencode({"q": "a&b"})                      # => 'q=a%26b'
f"https://api.example.com/search?{urlencode({'q': 'a b'})}"  # => 'https://api.example.com/search?q=a+b'
```

## Contract

- `key=value` を `&` でつないだ文字列を返す。先頭に `?` は付かない。空の辞書は `''`。順序は辞書の挿入順（組の列ならその順）
- `quote_plus` でエンコードする: 空白は `+`、`+` は `%2B`、`&` `=` `/` `?` `#` はパーセントエンコード、非 ASCII は UTF-8 のパーセントエンコード（`encoding` で変更可）。英数字と `_` `.` `-` `~` はそのまま。`*` `!` `'` `(` `)` はエンコードされる（`%2A` など）
- `quote_via=quote` にすると空白が `%20`（`+` は `%2B` のまま）。`safe="/"` でエンコードしない文字を増やせる
- 値は `str()` で文字列化される。`None` → `'None'`、`True` → `'True'`、`1.5` → `'1.5'`。`bytes` はそのままエンコード。省きたい値は先に除く
- `doseq=False`（既定）でリストを渡すと `str(list)` がエンコードされる（`tag=%5B%27a%27%2C+%27b%27%5D`）。`doseq=True` で要素ごとに `tag=a&tag=b`。空リストはキーごと消える。`doseq=True` でも `str` / `bytes` / `int` の値は 1 つの値として扱う（文字ごとに分解しない）
- キーも同じ規則でエンコードされる（`"a b"` → `a+b`）
- 辞書でも組の列でもないもの（文字列・平坦なリスト）は `TypeError`

## Alternatives

- 単一の値だけなら `quote_plus(s)` / `quote(s, safe="")`
- URL 全体に付けるなら `urlsplit(base)._replace(query=urlencode(...))` → `urlunsplit`
- `requests` の `params=` は同じ規則で、リストは `doseq=True` 相当（`tag=a&tag=b`）になる
- 入れ子（`a[b]=1`）や配列表記（`a[]=1`）は無い。必要ならキー名を自分で組む
- 解析は `parse_qs` / `parse_qsl`（url-parse-query）

## Pitfalls

- TypeScript（Node）の `URLSearchParams` とほぼ同じ規則（空白は `+`）だが、`*` は Python が `%2A`、JS がそのまま。`~` は Python がそのまま、JS が `%7E`。署名対象の文字列を両言語で揃えるときは注意
- `{"a": None}` は `a=None` になる（JS の `a=undefined` と同じ罠）。`{k: v for k, v in d.items() if v is not None}` で除く
- リストを渡すのに `doseq=True` を忘れると `tag=%5B%27a%27...` という Python の repr がそのまま送られる
- 空白を `%20` にしたい相手には `quote_via=quote`。既定の `+` を空白と解釈しない API もある

## Test

`examples/url-build-query_test.py`
