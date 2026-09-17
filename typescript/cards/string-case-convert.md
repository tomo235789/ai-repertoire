---
id: string-case-convert
lang: typescript
title: 文字列を kebab-case などの命名規則に変換する
tags: [命名規則, ケース変換, ケバブケース, キャメルケース, case-convert, kebab-case, camelCase, snake_case]
lib: es-toolkit
fn: kebabCase
since: "1.0.0"
verified: 2026-09-17
status: public
---

文字列を単語に分割し、kebab-case / camelCase / snake_case / PascalCase に組み直す。識別子や CSS クラス名、設定キーの表記統一に使う。

## Signature

```ts
function kebabCase(str: string): string
```

## Usage

```ts
import { camelCase, kebabCase, pascalCase, snakeCase } from 'es-toolkit';

kebabCase('userProfileURL');    // => 'user-profile-url'
camelCase('user_profile_url');  // => 'userProfileUrl'
snakeCase('UserProfileURL');    // => 'user_profile_url'
pascalCase('user-profile-url'); // => 'UserProfileUrl'
```

## Contract

- 純粋関数。どんな文字列を渡しても例外を投げない
- 単語の区切りは、区切り文字（空白・`-`・`_`・記号）、小文字→大文字の境界、数字の並び。数字は独立した単語になる（`version2Update` → `version-2-update`。camelCase では `version2Update`）
- 連続する大文字は略語として 1 語にまとめ、末尾の大文字の直後に小文字が続けばそこで分ける（`XMLHttpRequest` → `xml-http-request`）。`iOS` は `i-os`
- 区切り文字・記号は出力に残らないが、絵文字は 1 単語として残る（`hello 🐶 world` → `hello-🐶-world`。ZWJ で結合した絵文字列は要素ごとに分かれる）。空文字・空白のみ・記号のみは `''`
- 非 ASCII の文字（アクセント付き、日本語）も単語として残り、大小変換は `toLowerCase` / `toUpperCase` に従う。アクセントは除去されない
- 4 関数とも同じ単語分割（`words`）を使うので、分割結果は一致する

## Alternatives

- 単語分割だけ欲しいなら `words(str)`
- 先頭 1 文字だけ大文字にするなら `capitalize`（残りは小文字化）/ `upperFirst`（残りはそのまま）
- lodash 互換（アポストロフィを無視、アクセントを除去）が必要なら `es-toolkit/compat` の `kebabCase` / `camelCase`
- 区切り文字を変えたいなら `words(str).map((w) => w.toLowerCase()).join('.')`

## Pitfalls

- lodash（`es-toolkit/compat`）はアポストロフィを無視し（`Don't` → `dont`）、アクセントを除去する（`Crème` → `creme`）。es-toolkit 本体は `Don't` → `don-t`、`Crème` → `crème`
- 数字の前後で必ず分割されるので `md5` は `md-5`、`utf8` は `utf-8` になる。数字を含む語をそのまま保ちたい場合は自前で分割する
- `camelCase` の先頭単語は全体が小文字化される（`URLParser` → `urlParser`）
- `pascalCase` / `camelCase` は略語も先頭以外を小文字にする（`HTTPRequest` → `HttpRequest`）

## Test

`examples/string-case-convert.test.ts`
