---
id: string-truncate
lang: sql
title: 長い文字列を省略記号付きで切り詰める
tags: [切り詰め, 省略, 文字数制限, 部分文字列, truncate, ellipsis, substr, left]
lib: sqlite
fn: SUBSTR
since: "3.0"
verified: 2026-09-17
status: public
---

長さが上限を超える文字列だけ先頭 n 文字に切って省略記号を付ける。一覧画面のプレビューやログの要約に使う。

## Signature

```sql
CASE WHEN LENGTH(s) > n THEN SUBSTR(s, 1, n) || '...' ELSE s END
```

## Usage

```sql
WITH t(s) AS (VALUES ('hello world'), ('hi'), ('こんにちは世界'), (NULL))
SELECT s, CASE WHEN LENGTH(s) > 5 THEN SUBSTR(s, 1, 5) || '...' ELSE s END AS short
FROM t;
-- => ('hello world', 'hello...'), ('hi', 'hi'), ('こんにちは世界', 'こんにちは...'), (NULL, NULL)
```

## Contract

- `LENGTH(s) > n` のときだけ先頭 `n` 文字 + `'...'` になる（結果は `n + 3` 文字）。`n` 以下ならそのまま返し、省略記号は付かない。ちょうど `n` 文字も付かない
- `LENGTH` / `SUBSTR` はコードポイント単位（`'こんにちは'` は 5、`'😀'` は 1）。結合文字（`e` + U+0301）は 2 と数える（sqlite / duckdb とも）
- `NULL` は `NULL`（`LENGTH(NULL)` が `NULL` なので `ELSE` 側に落ちる）
- 省略記号込みで `n` 文字に収めるなら `SUBSTR(s, 1, n - 3) || '...'`（条件は `LENGTH(s) > n` のまま）
- `SUBSTR(s, start, len)` の `start` は 1 始まり。`start = 0` は「1 文字前」から数えるので `SUBSTR('hello', 0, 3)` は `'he'`（sqlite / duckdb とも）。負の `start` は末尾から（`SUBSTR('hello', -3)` → `'llo'`）
- `len` が元の長さより大きくてもエラーにならず全体を返す。`len` が `0` なら `''`。`len` が負なら `start` の **手前** `|len|` 文字を返す（`SUBSTR('hello', 3, -2)` → `'he'`、sqlite / duckdb とも）。`SUBSTR(s, 1, -1)` が `''` なのは 1 文字目の手前に何も無いからで、負の `len` が常に空になるわけではない
- `'…'`（U+2026）は 1 文字なので `n + 1` 文字に収まる
- sqlite は数値を渡すと文字列として扱う（`SUBSTR(12345, 1, 2)` → `'12'`、`LENGTH(123)` → `3`）。duckdb は VARCHAR が必要で整数は Binder Error
- 純粋関数。元の列は変わらない

## Alternatives

- duckdb / PostgreSQL / MySQL / BigQuery: `LEFT(s, n)`。sqlite には無い。duckdb の `LEFT('hello', -1)` は末尾 1 文字を除いた `'hell'`
- `SUBSTRING(s, 1, n)` は sqlite（3.34+）/ duckdb / PostgreSQL / MySQL で同じ
- 単語境界で切る（Python の `textwrap.shorten` 相当）は SQL の組み込みに無い。`INSTR` で最後の空白を探すか、アプリ側で行う
- バイト数で制限したいなら sqlite は `LENGTH(CAST(s AS BLOB))`、duckdb は `STRLEN(s)`（切り詰めもバイト境界を考える必要がある）

## Pitfalls

- TypeScript（es-toolkit/compat の `truncate`）は `length` に省略記号込みで収め、Python の `textwrap.shorten` は `width` 込みで単語境界で切る。この書き方は本文 `n` 文字 + 省略記号なので、上限が「表示全体の長さ」なら `n - 3` にする
- `SUBSTR` は 1 始まり。JavaScript の `slice(0, n)` の癖で `SUBSTR(s, 0, n)` と書くと 1 文字少なくなる（エラーにはならない）
- `LENGTH` はコードポイント数であって表示幅でもバイト数でもない。VARCHAR(n) 列のバイト制限に合わせたいときは別途バイト数を見る
- sqlite の `LENGTH` はテキストに埋め込まれた NUL 文字までしか数えない（`'a' || char(0) || 'b'` は 1）

## Test

`examples/string-truncate_test.py`
