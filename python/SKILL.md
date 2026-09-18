---
name: py-repertoire
description: Python でイテラブル・辞書・文字列・日付・非同期のユーティリティを書く前に読む。自前実装せず標準ライブラリ（itertools / functools / datetime / asyncio）や more-itertools などの既存関数へ誘導する
---

# py-repertoire

Python で「ちょっとしたユーティリティ」を書きたくなったら、実装する前にこの Skill の手順に従う。

## 手順

1. `cards/` の frontmatter `tags` と `title` を用途語（日本語・英語どちらでも）で検索する
   - 例: 「重複除去」「dedupe」「chunk」「分割」
2. 該当カードがあれば、その `## Signature` と `## Contract` に従って既存関数を使う。`## Usage` をそのまま貼れる
3. 該当がなければ自前実装してよい。ただし同じ形式のカードを `status: public` で `cards/` に提案する（PR テンプレートの抽象化チェックリストを通す）（`../schema/card.schema.json` と `../README.md` の「カードの書き方」を参照）
4. `lint/ruff.toml` の禁止 API（`TID251`）に触れたら、message に書かれたカード ID の関数へ置き換える

## カード一覧

`cards/` 配下。ファイル名 = カード ID（TypeScript と同じ ID）。機能別の言語横断リファレンスは生成物 `reference/<id>.md` にある。

| 領域 | ID |
|---|---|
| collection | chunk, dedup-by-key, group-by, partition, zip, flatten, sort-by, sliding-window, take-while |
| object | pick, omit, deep-merge, map-values, invert |
| string | case-convert, pad, truncate, slugify, template |
| number | clamp, round-to, sum-by, mean |
| date | format-iso, add-days, diff-days, start-of-day, tz-convert |
| function | memoize, once, pipe（debounce / throttle は Python に標準的な実装が無いため無し） |
| async | sleep, timeout, retry, limit-concurrency |
| result | try-to-result |
| iter | lazy-map, lazy-filter, take, to-array, range |
| map / set | map-group-to-map, map-count-by, map-key-by, set-union, set-difference |
| validation | parse-schema, safe-parse, coerce-number, email, brand-type |
| json | parse-safe, stringify-stable, deep-equal, clone |
| io | read-lines, write-atomic, join-path, glob, temp-dir |
| url | join-path, build-query, parse-query, normalize, is-absolute |
| http | retry-idempotent, timeout, pagination-cursor, fetch-json-typed, rate-limit-backoff |
| error | custom-class, cause-chain, aggregate, assert-never, invariant |
| log | structured, redact-secrets, correlation-id |

## 参照先ライブラリ

| 領域 | 既定 |
|---|---|
| collection / object | stdlib（itertools, functools, operator）、足りなければ more-itertools |
| string / number | stdlib（str, statistics, decimal） |
| date | stdlib（datetime, zoneinfo）。naive な `datetime.now()` は使わない |
| function / async / http | stdlib（functools, asyncio）。リトライは tenacity、HTTP は httpx |
| validation | pydantic |
| io / url / json / error / log | stdlib（pathlib, tempfile, urllib.parse, json, contextvars, logging） |
