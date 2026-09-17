---
id: string-case-convert
lang: python
title: 文字列を kebab-case などの命名規則に変換する
tags: [命名規則, ケース変換, スネークケース, キャメルケース, case-convert, snake_case, camelCase, kebab-case]
lib: inflection
fn: underscore
since: "0.5"
verified: 2026-09-17
status: public
---

CamelCase や kebab-case の文字列を snake_case に分解し、`camelize` / `dasherize` / `titleize` で別の命名規則に組み直す。識別子や設定キーの表記統一に使う。

## Signature

```python
inflection.underscore(word: str) -> str
```

## Usage

```python
from inflection import camelize, dasherize, titleize, underscore

underscore("userProfileURL")               # => 'user_profile_url'
camelize("user_profile_url")               # => 'UserProfileUrl'
camelize("user_profile_url", False)        # => 'userProfileUrl'
dasherize(underscore("XMLHttpRequest"))    # => 'xml-http-request'
titleize("user_profile_url")               # => 'User Profile Url'
```

## Contract

- 純粋関数。`str` 以外を渡すと `TypeError`（`underscore(None)`）。空文字は `''`
- `underscore` の区切り位置は 3 つ: 小文字または数字→大文字の境界（`aB` → `a_b`、`version2Update` → `version2_update`）、連続大文字の末尾で次に小文字が続く位置（`XMLHttpRequest` → `xml_http_request`、`iOS` → `i_os`）、`-`（`_` に置換）。その後全体を小文字化する
- 小文字→数字の境界では分割しない（`md5` → `md5`、`html5Parser` → `html5_parser`）
- 空白・`.`・記号・アポストロフィ・絵文字はそのまま残る（`user profile` → `user profile`、`Don't` → `don't`）
- 非 ASCII は `str.lower` で小文字化され、アクセントは除去されない（`Crème` → `crème`、日本語はそのまま）
- `camelize` は `_` と先頭だけを区切りと見なし、大文字境界では分割しない（`camelize("userProfileURL")` → `'UserProfileURL'`）。`dasherize` は `_` → `-` の置換のみ。CamelCase から kebab-case にするには `dasherize(underscore(s))` と重ねる
- `camelize("", False)` は `IndexError` を投げる（`uppercase_first_letter=True` なら `''`）

## Alternatives

- 単語の連結と区切りの正規化まで欲しい（空白・記号を区切りとして扱う）なら `python-slugify` の `slugify(s, separator="_")`（`string-slugify`）
- 先頭だけ大文字にするなら stdlib の `str.capitalize`（残りは小文字化）
- 表示用の「先頭大文字 + 空白区切り」は `humanize`（末尾の `_id` を落とす）

## Pitfalls

- TypeScript（es-toolkit）の `kebabCase` は空白・記号・数字の前後すべてを区切りにするが、`underscore` は大文字境界と `-` しか見ない。`user profile` は `user profile` のまま、`md5` は `md5` のまま（es-toolkit は `md-5`）
- 連続大文字の末尾規則は末尾側から効くので `ABCdef` → `ab_cdef`
- `titleize` / `humanize` は末尾の `_id` を落とす（`titleize("userID")` → `'User'`、`titleize("user_id")` → `'User'`）。ID を含む文字列に使わない
- `camelize` の先頭単語は `uppercase_first_letter=False` でも先頭 1 文字だけ小文字化される（`camelize("URLParser", False)` → `'uRLParser'`）。先に `underscore` を通す

## Test

`examples/string-case-convert_test.py`
