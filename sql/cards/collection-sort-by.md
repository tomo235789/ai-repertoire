---
id: collection-sort-by
lang: sql
title: 複数のキーで配列を昇順に並べ替える
tags: [並べ替え, ソート, 整列, 照合順序, sort, order-by, nulls-last, collate]
lib: sqlite
fn: ORDER BY
since: "3.30"
verified: 2026-09-17
status: public
---

複数の列で結果を昇順に並べる。`NULL` の位置と文字列の大小比較は方言で違うので明示する。

## Signature

```sql
ORDER BY key1 [ASC | DESC] [NULLS FIRST | NULLS LAST], key2, ...
```

## Usage

```sql
WITH t(name, age) AS (VALUES ('b', 30), ('a', 30), ('c', 20), ('d', NULL))
SELECT name, age FROM t ORDER BY age NULLS LAST, name;
-- => ('c', 20), ('a', 30), ('b', 30), ('d', NULL)
```

## Contract

- 左のキーから順に比較し、等しいときだけ次のキーで比較する。既定は `ASC`（昇順）
- すべてのキーが等しい行同士の順序は不定。テーブルの行に「元の順序」は無いので安定ソートの概念も無い。順序を固定するなら一意な列（ID）を最後のキーに足す
- `NULL` の既定位置は方言で違う。sqlite は `NULL` を最小値として扱う（`ASC` で先頭、`DESC` で末尾）。duckdb は既定が `NULLS LAST` で方向によらず末尾。`NULLS FIRST` / `NULLS LAST` を書けばどちらでも同じになる（sqlite は 3.30+）
- 文字列は既定でバイト順。大文字が小文字より前に来る（`'A' < 'B' < 'a' < 'b'`）。`COLLATE NOCASE` で大小を無視できる（sqlite、duckdb で確認）。NOCASE で等しい `'a'` と `'A'` の順序は不定
- 数値が文字列型で入っていると辞書順になる（`'200' < '30' < '9'`）。数値で並べるなら列を数値型にするか `CAST(age AS INTEGER)`
- サブクエリの `ORDER BY` は外側の結果の順序を保証しない。順序が要る所（最外側）で書く
- `ORDER BY 2, 1` のように列番号でも指定できる
- 0 行なら 0 行。`ORDER BY` 無しの結果順は不定

## Alternatives

- PostgreSQL: `NULLS LAST` が書け、既定は `NULL` が最大（`ASC` で末尾、`DESC` で先頭）と書かれる。MySQL: `NULL` は最小で `NULLS LAST` 構文が無い
- 方言を問わず `NULL` を末尾にするなら `ORDER BY age IS NULL, age`（sqlite / duckdb で確認）
- 大小無視は `ORDER BY LOWER(name), name` でも書ける（PostgreSQL / duckdb / sqlite）。MySQL は既定の照合順序が大小を無視する
- 上位 n 件は `ORDER BY ... LIMIT n`、最小の 1 件だけなら `LIMIT 1`
- キーごとに昇降を変えるなら `ORDER BY age DESC, name ASC`

## Pitfalls

- TypeScript の `sortBy` / Python の `sorted` は安定ソートで同順位の入力順を保つが、SQL は保証しない。ページングで `LIMIT` / `OFFSET` を使うなら一意キーまで並べないと行が重複・欠落する
- es-toolkit の `sortBy` は `null` / `undefined` を常に末尾に置き、Python は `None` が混ざると `TypeError`。SQL は方言ごとに既定が違うので `NULLS LAST` か `IS NULL` を明示する
- 文字列の比較は照合順序（collation）次第。同じクエリでも DB や列の定義で結果が変わり得る
- `ORDER BY` を書き忘れると sqlite / duckdb とも「たまたま」入力順に見えることが多く、テストで気付きにくい

## Test

`examples/collection-sort-by_test.py`
