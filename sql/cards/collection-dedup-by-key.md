---
id: collection-dedup-by-key
lang: sql
title: キー関数で配列の重複を除去する
tags: [重複除去, ユニーク, 一意化, 窓関数, dedupe, distinct, row-number, first-per-group]
lib: sqlite
fn: ROW_NUMBER() OVER
since: "3.25"
verified: 2026-09-17
status: public
---

キー列ごとに 1 行だけ残す。「顧客ごとに最新の注文」「ID ごとに最初のログ」のような「各キーの代表行」を取るときに使う。

## Signature

```sql
ROW_NUMBER() OVER (PARTITION BY key ORDER BY sort_col)
```

## Usage

```sql
WITH t(id, name, ts) AS (VALUES (1, 'a', 3), (2, 'b', 1), (1, 'c', 2))
SELECT id, name
FROM (SELECT id, name, ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts) AS rn FROM t)
WHERE rn = 1
ORDER BY id;
-- => (1, 'c'), (2, 'b')   -- id ごとに ts が最小の行
```

## Contract

- `PARTITION BY` のキーごとにちょうど 1 行残る。残る行は `OVER` の `ORDER BY` で決まる（昇順なら最小、`DESC` なら最大）
- `OVER` の `ORDER BY` を省くと、どの行が `rn = 1` になるかは不定。実行ごと・DB ごとに変わり得るので必ず書く
- `ORDER BY` の値が同じ行が複数あるときも、どれが 1 になるかは不定。一意になる列（自増 ID など）を末尾に足す
- キーが `NULL` の行同士は同じグループになり、1 行残る（sqlite / duckdb とも）
- 窓関数は `WHERE` に直接書けない。サブクエリか CTE で `rn` を出してから絞る（duckdb は `QUALIFY ROW_NUMBER() OVER (...) = 1` で 1 段で書ける。sqlite に `QUALIFY` は無い）
- 列の値・型はそのまま。外側に `ORDER BY` を書かないと結果の順序は保証されない
- 0 行なら 0 行

## Alternatives

- duckdb / PostgreSQL: `SELECT DISTINCT ON (id) id, name FROM t ORDER BY id, ts`。`ORDER BY` の先頭が `DISTINCT ON` の列でなければならない。sqlite / MySQL では構文エラー
- duckdb / BigQuery / Snowflake: `SELECT id, name FROM t QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts) = 1`
- MySQL 8.0+ は同じ `ROW_NUMBER` が書ける。5.7 には窓関数が無いので `WHERE NOT EXISTS (SELECT 1 FROM t AS u WHERE u.id <=> t.id AND ((NOT u.ts <=> t.ts AND (u.ts IS NULL OR (t.ts IS NOT NULL AND u.ts < t.ts))) OR (u.ts <=> t.ts AND u.pk < t.pk)))` と書く（`pk` は一意な列）。`u.id = t.id` だと `NULL` キーの行が全部残り、`u.ts < t.ts` だけだと `ts` が同じ行や `ts` が `NULL` の行が複数残るので、`ROW_NUMBER() = 1` と同じ結果にするには（並べ替えは `NULL` を最小として扱う。sqlite と MySQL の昇順は既定で `NULL` が先、duckdb / PostgreSQL は `NULLS FIRST` を明示する。MySQL は `NULLS FIRST` 構文を持たないので書かない）、キーと並べ替え列の両方を NULL 安全に比較（MySQL は `<=>`）し、`NULL` を最小として扱い、一意なタイブレークを入れる。同じ形を sqlite は `IS`、duckdb は `IS NOT DISTINCT FROM` で書け、`ROW_NUMBER` 版と一致することを確認した
- 「最後の行」は `ORDER BY ts DESC`。「各キーの上位 n 件」は `WHERE rn <= n`
- キーの重複を消したいだけ（他の列が要らない）なら `SELECT DISTINCT id FROM t`

## Pitfalls

- TypeScript の `uniqBy` / Python の `unique_everseen` は **入力順で最初** の要素を残すが、SQL のテーブルに順序は無い。「最初」を表す列（時刻、自増 ID）が要る
- `SELECT id, MIN(ts), name FROM t GROUP BY id` は sqlite では通り、`MIN` / `MAX` が 1 つだけのときは `name` にその行の値が入る（sqlite 固有の特例）。duckdb は `column "name" must appear in the GROUP BY clause` でエラー、MySQL は設定次第で不定値になる。移植性のある書き方は `ROW_NUMBER`
- `WHERE ROW_NUMBER() OVER (...) = 1` は構文エラー（`WHERE` は窓関数より先に評価される）。サブクエリにする
- 複合キーは `PARTITION BY a, b`。文字列連結でキーを作らない（区切り文字の衝突）

## Test

`examples/collection-dedup-by-key_test.py`
