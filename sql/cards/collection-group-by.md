---
id: collection-group-by
lang: sql
title: キー関数で配列をグループ化する
tags: [グループ化, 分類, 集計, 連結, group-by, aggregate, count, string-agg]
lib: sqlite
fn: GROUP BY
since: "3.0"
verified: 2026-09-17
status: public
---

キー列が同じ行を 1 グループにまとめ、グループごとに件数・合計・連結などの集計値を 1 行で返す。種別ごとの集計や画面のセクション分けに使う。

## Signature

```sql
SELECT key, AGG(col) FROM t GROUP BY key [HAVING cond] ORDER BY key
```

## Usage

```sql
WITH t(k, v) AS (VALUES ('a', 1), ('b', 2), ('a', 3), (NULL, 4))
SELECT k, COUNT(*) AS n, SUM(v) AS total, GROUP_CONCAT(v, ',') AS items
FROM t
GROUP BY k
ORDER BY k;
-- => (NULL, 1, 4, '4'), ('a', 2, 4, '1,3'), ('b', 1, 2, '2')   -- duckdb は NULL が末尾。'1,3' の連結順は保証されない
```

## Contract

- 同じ `k` の行が 1 グループになり、グループごとに 1 行返る。`NULL` のキーは互いに等しいものとして 1 グループになる（sqlite / duckdb とも）
- 結果の順序は保証されない。`ORDER BY` を書く。`ORDER BY k` を書いても `NULL` キーの位置は方言で違う（sqlite は先頭、duckdb は末尾。collection-sort-by 参照）
- `COUNT(*)` は `NULL` の値も含む行数、`COUNT(v)` / `SUM(v)` は `NULL` を無視する
- `GROUP_CONCAT(v, ',')` の連結順は不定。順序が要るなら `GROUP_CONCAT(v, ',' ORDER BY v)`（sqlite 3.44+、duckdb）。3.44 未満は構文エラーになるので、ウィンドウ形式 `SELECT DISTINCT k, GROUP_CONCAT(v, ',') OVER (PARTITION BY k ORDER BY v ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)` でウィンドウの `ORDER BY` に入力順を指定する（sqlite 3.25+ / duckdb）。`FROM (SELECT k, v FROM t ORDER BY k, v)` と並べ替えたサブクエリから集計する形は sqlite 3.37 / 3.45 / 3.53 と duckdb 1.5 でその順に連結されたが、規格上の保証は無い。duckdb では `STRING_AGG(v, ',')` が正式名で `GROUP_CONCAT` は別名として通る
- 入力が 0 行ならグループが無いので 0 行。`GROUP BY` 無しの集計だけなら 1 行（`COUNT(*)` は `0`、`SUM` は `NULL`）
- `SELECT` にキーでも集計でもない列（裸の列）を書くと、sqlite は通るがグループ内のどの行の値かは不定（`MIN` / `MAX` が 1 つだけのときはその行の値になる特例あり）。duckdb は `must appear in the GROUP BY clause` でエラー（`ANY_VALUE(v)` を書けば通る）
- キーの比較は値の等価性。`1` と `1.0` は同じグループ、`'a'` と `'A'` は別グループ
- `HAVING` はグループ化後の絞り込み（`HAVING COUNT(*) > 1`）。`WHERE` はグループ化前

## Alternatives

- PostgreSQL: `STRING_AGG(v::text, ',' ORDER BY v)`、配列で受けるなら `ARRAY_AGG(v ORDER BY v)`。MySQL: `GROUP_CONCAT(v ORDER BY v SEPARATOR ',')`。BigQuery: `STRING_AGG(CAST(v AS STRING), ',' ORDER BY v)` / `ARRAY_AGG(v)`
- duckdb はリストで受けるなら `LIST(v ORDER BY v)`
- 条件付きの件数は `COUNT(*) FILTER (WHERE cond)`（collection-partition）
- 複数キーは `GROUP BY k1, k2`。キーを式で作るなら `GROUP BY SUBSTR(k, 1, 1)` のように式をそのまま書く
- 件数だけならグループ化せず `SELECT COUNT(DISTINCT k)`

## Pitfalls

- TypeScript の `groupBy` / Python の `map_reduce` はキーの初出順とグループ内の入力順を保つが、SQL は保たない。グループ内の順序は `GROUP_CONCAT(... ORDER BY ...)` で、グループの順序は外側の `ORDER BY` で指定する
- es-toolkit の `groupBy` は数値キーを文字列化して `1` と `'1'` を同じグループにするが、SQL は型どおり比較する（sqlite は数値と文字列を別、duckdb は型が合わないとエラーか暗黙変換）
- `GROUP_CONCAT` の区切りは既定 `,`。値に `,` が含まれると分割できなくなる。構造を保つなら duckdb の `LIST` / PostgreSQL の `ARRAY_AGG`
- MySQL は `ONLY_FULL_GROUP_BY` が無効だと裸の列が通って不定値を返す。sqlite も同じ。列を出したいなら集計関数で包むか、collection-dedup-by-key の `ROW_NUMBER` で代表行を選ぶ

## Test

`examples/collection-group-by_test.py`
