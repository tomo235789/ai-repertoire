---
id: string-pad
lang: sql
title: 文字列を指定幅まで両側に埋める
tags: [パディング, ゼロ埋め, 桁揃え, 幅, pad, lpad, rpad, zero-fill]
lib: duckdb
fn: LPAD
since: "1.0"
verified: 2026-09-17
status: public
---

文字列の左（`LPAD`）または右（`RPAD`）に埋め文字を足して指定の長さにする。連番のゼロ埋めや固定長レコードの整形に使う。SQL 標準に両側埋めは無い。

## Signature

```sql
LPAD(s, n, fill)   -- RPAD(s, n, fill)
```

## Usage

```sql
SELECT LPAD('42', 5, '0'), RPAD('42', 5, '0'), LPAD('abcdefg', 5, '0'), LPAD('ab', 6, 'xy');
-- => ('00042', '42000', 'abcde', 'xyxyab')   -- 幅を超えると切り詰められる
```

## Contract

- `fill` を繰り返して長さ `n` にする。`LPAD` は左に、`RPAD` は右に足す
- `LENGTH(s) > n` なら **先頭 `n` 文字に切り詰める**。`LPAD` でも `RPAD` でも先頭側が残る（`LPAD('abcdefg', 5, '0')` → `'abcde'`、`RPAD('abcdefg', 5, '0')` → `'abcde'`）
- `n <= 0` なら `''`（`LPAD('ab', 0, 'x')` → `''`、`n = -1` も `''`）。`n = LENGTH(s)` ならそのまま
- `fill` が複数文字なら繰り返し、端数は `fill` の先頭から切る（`LPAD('ab', 5, 'xy')` → `'xyxab'`、`RPAD('ab', 5, 'xy')` → `'abxyx'`）
- `fill` が `''` で埋めが必要なら `Insufficient padding` エラー。埋めが不要（長さが足りている）ならエラーにならない
- 長さはコードポイント単位。`LPAD('あ', 3, '*')` → `'**あ'`、`LPAD('😀', 3, '*')` → `'**😀'`。結合文字（`e` + U+0301）は 2 文字と数え `LPAD('e' || chr(769), 3, '*')` → `'*é'`
- どの引数も `NULL` なら `NULL`
- `s` は文字列型が必要。整数を渡すと Binder Error（`LPAD(42::VARCHAR, 5, '0')` と書く）
- 返り値は VARCHAR。純粋関数

## Alternatives

- sqlite に `LPAD` / `RPAD` は無い。数値のゼロ埋めは `printf('%05d', n)`（`-42` は `'-0042'`、幅を超えても切り詰めず `'123456'`）、文字列は `SUBSTR('00000' || s, -5)`（幅を超えると **末尾** 5 文字が残る。`LPAD` とは切り詰め方向が逆）、右埋めは `printf('%-5s', s)`。`printf('%5s', s)` はバイト幅で数えるので全角文字が混ざると揃わない（`printf('%5s|', 'あい')` → `'あい|'`）
- PostgreSQL / MySQL / BigQuery: 同じ `LPAD(s, n, fill)` / `RPAD(s, n, fill)`。幅を超えると切り詰めると書かれる。MySQL は `fill` を省略できない、PostgreSQL は省略すると空白
- duckdb / PostgreSQL の書式指定 `format('{:05d}', 42)`（duckdb）/ `printf('%05d', 42)`（duckdb、sqlite）
- 両側に埋める（センタリング）は自前で `LPAD(RPAD(s, CAST((LENGTH(s) + n) // 2 AS INTEGER), ' '), n, ' ')`（余りの 1 文字は左に付く。`'abc'`, `n = 8` → `'   abc  '`）。duckdb の `LPAD` / `RPAD` の幅は INTEGER 限定で、`LENGTH` は BIGINT、`/` は DOUBLE を返すので `CAST` 無しでは Binder Error（1.5 で確認）

## Pitfalls

- TypeScript（es-toolkit の `pad`）/ Python の `str.center` は幅を超えても切り詰めないが、`LPAD` / `RPAD` は切り詰める。ID の桁数が想定を超えたときに静かにデータが欠ける。`LENGTH(s) > n` の行を先に検出する
- es-toolkit の `pad` は両側、Python の `center` も両側だが、SQL は片側ずつ。中央寄せは自前で組む
- 全角文字も 1 と数えるので表示幅は揃わない。等幅で揃えるには表示幅の計算がアプリ側で要る
- sqlite の `SUBSTR('00000' || s, -5)` は幅を超えたとき末尾が残る（先頭が消える）。`LPAD` の移植のつもりで使うと切り詰め方向が違う

## Test

`examples/string-pad_test.py`
