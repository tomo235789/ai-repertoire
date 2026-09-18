---
id: collection-partition
lang: sql
title: 条件で配列を 2 つに振り分ける
tags: [振り分け, 条件付き集計, 二分, partition, filter, conditional-aggregate, count-if]
lib: sqlite
fn: FILTER
since: "3.30"
verified: 2026-09-17
status: public
---

条件を満たす行と満たさない行をそれぞれ集計して 1 行で返す。「有効 / 無効の件数」「成功額と失敗額」を 1 クエリで出すときに使う。

## Signature

```sql
AGG(col) FILTER (WHERE cond)
```

## Usage

```sql
WITH t(v) AS (VALUES (1), (2), (3), (4), (NULL))
SELECT COUNT(*) FILTER (WHERE v % 2 = 0) AS evens,
       COUNT(*) FILTER (WHERE NOT (v % 2 = 0)) AS odds,
       COUNT(*) AS total
FROM t;
-- => (2, 2, 5)   -- NULL はどちらにも入らない
```

## Contract

- `FILTER (WHERE cond)` は `cond` が真の行だけを集計に渡す。`COUNT(*) FILTER (...)` は条件を満たす行数
- `cond` が `NULL`（不明）になる行は真側にも `NOT cond` 側にも入らない。両側の合計は `COUNT(*)` と一致しないことがある。全行をどちらかに入れるなら偽側を `NOT COALESCE(cond, FALSE)` か `cond IS NOT TRUE` にする（sqlite / duckdb で確認）
- 該当行が 0 件のとき `COUNT` は `0`、`SUM` / `AVG` は `NULL`
- 入力が 0 行でも `GROUP BY` が無ければ 1 行返る（`COUNT` は `0`）
- `SUM` / `GROUP_CONCAT` など任意の集計関数に付けられ、`GROUP BY` と組み合わせるとグループごとの条件付き集計になる。窓関数 `AGG(...) FILTER (...) OVER (...)` も書ける（sqlite / duckdb で確認）
- 順序の概念は無い。`GROUP_CONCAT ... FILTER` の連結順は不定
- sqlite は 3.30 以降。duckdb / PostgreSQL 9.4 以降は同じ構文

## Alternatives

- MySQL（`FILTER` 非対応）は `SUM(CASE WHEN cond THEN 1 ELSE 0 END)`。BigQuery は `COUNTIF(cond)` / `SUM(IF(cond, v, 0))` と書く
- `SUM(CASE WHEN cond THEN 1 ELSE 0 END)` は sqlite / duckdb でも通り、`COUNT(*) FILTER` と同じ値になる。`ELSE 0` を省くと該当 0 件で `NULL`
- 行そのものを 2 つの結果集合に分けたいなら `WHERE cond` と `WHERE NOT cond` の 2 クエリ、または `CASE WHEN cond THEN 'yes' ELSE 'no' END AS side` を作って `GROUP BY side`（collection-group-by）
- 「真の割合」は `AVG(CASE WHEN cond THEN 1.0 ELSE 0 END)`

## Pitfalls

- TypeScript の `partition` / Python の `more_itertools.partition` は要素の配列を 2 つ返すが、SQL の `FILTER` が返すのは集計値。要素（行）を残したいなら `CASE` でラベル列を作る
- Python の `partition` は `(偽, 真)`、es-toolkit は `[真, 偽]` の順で返すが、SQL は列の並び順を自分で決める。列名（`evens` / `odds`）を付けて取り違えを防ぐ
- 3 値論理: `NOT cond` は `cond` が `NULL` の行を拾わない。アプリ言語の `!pred(x)` のつもりで書くと `NULL` の行が消える
- `COUNT(v) FILTER (...)` は `v` が `NULL` の行を数えない。行数なら `COUNT(*)`

## Test

`examples/collection-partition_test.py`
