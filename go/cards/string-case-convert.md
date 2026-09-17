---
id: string-case-convert
lang: go
title: 文字列を kebab-case などの命名規則に変換する
tags: [命名規則, ケース変換, ケバブケース, キャメルケース, case-convert, kebab-case, camelCase, snake_case]
lib: samber/lo
fn: lo.KebabCase
since: "1.38"
verified: 2026-09-17
status: public
---

文字列を単語に分割し、kebab-case / camelCase / snake_case / PascalCase に組み直す。識別子や CSS クラス名、設定キーの表記統一に使う。

## Signature

```go
func KebabCase(str string) string
```

## Usage

```go
import "github.com/samber/lo"

lo.KebabCase("userProfileURL")    // => "user-profile-url"
lo.CamelCase("user_profile_url")  // => "userProfileUrl"
lo.SnakeCase("UserProfileURL")    // => "user_profile_url"
lo.PascalCase("user-profile-url") // => "UserProfileUrl"
```

## Contract

- 純粋関数。どんな文字列を渡しても panic しない。空文字・空白のみ・記号のみは `""`
- 単語の区切りは、文字でも数字でもない文字（空白・`-`・`_`・`.`・アポストロフィ）、小文字→大文字の境界、数字と文字の境界。`KebabCase` / `SnakeCase` では数字が独立した単語になる（`version2Update` → `version-2-update`、`md5` → `md-5`）
- 連続する大文字は略語として 1 語にまとめ、末尾の大文字の直後に小文字が続けばそこで分ける（`XMLHttpRequest` → `xml-http-request`、`iOS` → `i-os`、`ABCdef` → `ab-cdef`）
- `CamelCase` / `PascalCase` は数字の単語を直前の単語に連結し、次の単語の頭を大文字にする（`version2Update` → `version2Update`、`md5` → `md5`、`a1b2` → `a1B2`）
- `CamelCase` は先頭の単語を全部小文字にし、`PascalCase` は各単語を先頭大文字 + 残り小文字にする。略語も先頭以外は小文字になる（`URLParser` → `urlParser`、`HTTPRequest` → `HttpRequest`）
- 記号・絵文字は出力に残らない（`hello 🐶 world` → `hello-world`、`Don't` → `don-t`）
- 非 ASCII の文字（アクセント付き、日本語）は単語として残り、Unicode の規則で大小変換される。アクセントは除去されない（`Crème Brûlée` → `crème-brûlée`）
- 4 関数とも同じ単語分割 `lo.Words` を使うので、分割結果は一致する

## Alternatives

- 単語分割だけ欲しいなら `lo.Words(str)`（`[]string`）
- 区切り文字を変えたいなら `strings.Join(lo.Map(lo.Words(s), func(w string, _ int) string { return strings.ToLower(w) }), ".")`
- 大小変換だけなら stdlib の `strings.ToLower` / `strings.ToUpper`

## Pitfalls

- 絵文字の扱いが違う。TypeScript（es-toolkit の `kebabCase`）は絵文字を 1 単語として残す（`hello-🐶-world`）が、lo は落とす。Python（inflection の `underscore`）は空白や数字の前後で分割しない（`md5` は `md5` のまま）
- `KebabCase` / `SnakeCase` では数字が独立の単語になり、`md5` は `md-5`、`utf8` は `utf_8` になる。数字を含む語をそのまま保ちたい場合は自前で分割する
- `CamelCase` / `PascalCase` は略語も先頭以外を小文字にする（`HTTPRequest` → `httpRequest` / `HttpRequest`）。元の大文字は復元できない
- 先頭が数字の文字列は `CamelCase` でも大文字始まりになる（`1st place` → `1StPlace`）

## Test

`examples/string-case-convert_test.go`
