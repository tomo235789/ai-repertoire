---
id: url-parse-query
lang: python
title: クエリ文字列を解析する
tags: [クエリ文字列, URLデコード, 検索パラメータ, 複数値, query-string, url-decode, search-params, parse-query]
lib: stdlib
fn: urllib.parse.parse_qs
since: "3.0"
verified: 2026-09-17
status: public
---

`a=1&a=2&q=x+y` の形のクエリ文字列からキーごとの値を取り出す。リクエストの URL やリダイレクト先の解析に使う。

## Signature

```python
urllib.parse.parse_qs(qs, keep_blank_values=False, strict_parsing=False, encoding='utf-8', errors='replace', max_num_fields=None, separator='&')
```

## Usage

```python
from urllib.parse import parse_qs, parse_qsl, urlsplit

qs = urlsplit("https://example.com/search?q=foo+bar&tag=a&tag=b&page=2&empty=").query
parse_qs(qs)                   # => {'q': ['foo bar'], 'tag': ['a', 'b'], 'page': ['2']}（値は常にリスト）
parse_qs(qs)["page"][0]        # => '2'（文字列。数値にはならない）
parse_qs(qs).get("missing")    # => None
parse_qs(qs, keep_blank_values=True)["empty"]  # => ['']（既定では empty は捨てられる）
parse_qsl(qs)                  # => [('q', 'foo bar'), ('tag', 'a'), ('tag', 'b'), ('page', '2')]
dict(parse_qsl(qs))            # => {'q': 'foo bar', 'tag': 'b', 'page': '2'}（重複キーは最後が勝つ）
```

## Contract

- `parse_qs` は `dict[str, list[str]]`。1 つしか無いキーも `['2']` とリスト。キーの順序は最初に出現した順。`parse_qsl` は `(key, value)` の組のリストで出現順
- 値は常に `str`。数値・真偽値には変換しない
- `+` と `%20` は空白に、`%XX` は `encoding`（既定 UTF-8）でデコードされる。キーも同様。不正な `%`（`%zz` や単独の `%`）は例外にならずそのまま残り、不正な UTF-8 は既定 `errors='replace'` で U+FFFD（`errors='strict'` で `UnicodeDecodeError`）
- 空の値（`a=` や `=` 無しの `a`）は既定で捨てる。`keep_blank_values=True` で `['']` として残す。`strict_parsing=True` にすると `=` の無いフィールドと空フィールド（`&&`）で `ValueError`（`a=` は通る）
- 区切りは `&` だけ。`;` は区切りにならず値の一部になる（`separator=";"` で変更可）。`a=b=c` は最初の `=` で分けて値 `'b=c'`
- 先頭の `?` は取り除かない（キーが `'?a'` になる）。`#f` も取り除かない（値が `'1#f'`）。URL 全体は `urlsplit(url).query` で取り出してから渡す
- `max_num_fields` を超える個数のフィールドがあると `ValueError`（DoS 対策）
- 空文字列は `{}` / `[]`。`bytes` を渡せばキーと値も `bytes`

## Alternatives

- 単一の値のデコードは `unquote_plus`（`+` も空白に）/ `unquote`（`+` はそのまま）。どちらも不正な `%` で例外にならない
- 入れ子表記 `a[b]=1` はキー `'a[b]'` のまま。展開が要るなら自前で
- 組み立ては `urlencode`（url-build-query）。`urlencode(parse_qsl(qs))` で往復できる

## Pitfalls

- TypeScript（Node）の `URLSearchParams.get` は最初の値を文字列で返し空値も残すが、`parse_qs` は **常にリスト**で空値を既定で捨てる。`[0]` を忘れると `['foo bar']` を文字列として扱ってしまう
- 無いキーは `KeyError`。`.get("k", [""])[0]` か、`dict(parse_qsl(qs))` で単一値の辞書にしてから `.get`
- `dict(parse_qsl(qs))` は複数値を潰す（最後が勝つ）。チェックボックスやタグなど複数値のキーは `parse_qs` で取る
- `"?a=1"` をそのまま渡すとキーが `'?a'` になる。`urlsplit` を通す
- `int(parse_qs(qs)["page"][0])` は数値でないとき `ValueError`。外部入力は validation-coerce-number で検証する

## Test

`examples/url-parse-query_test.py`
