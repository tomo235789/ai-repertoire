---
id: date-format-iso
lang: sql
title: 日付を ISO 8601 形式の文字列にする
tags: [日付書式, ISO8601, UTC, タイムスタンプ, format, strftime, iso-8601, timestamp]
lib: sqlite
fn: STRFTIME
since: "3.0"
verified: 2026-09-17
status: public
---

日時を `2024-02-29T13:45:07Z` の形の文字列にする。API のレスポンスやログの時刻表記に使う。sqlite の日時は UTC 前提なので `Z` をリテラルで付ける。

## Signature

```sql
STRFTIME('%Y-%m-%dT%H:%M:%SZ', ts)
```

## Usage

```sql
SELECT STRFTIME('%Y-%m-%dT%H:%M:%SZ', '2024-02-29 13:45:07'),
       STRFTIME('%Y-%m-%dT%H:%M:%SZ', '2024-02-29 13:45:07+09:00'),
       STRFTIME('%Y-%m-%dT%H:%M:%SZ', 1709214307, 'unixepoch');
-- => ('2024-02-29T13:45:07Z', '2024-02-29T04:45:07Z', '2024-02-29T13:45:07Z')
```

## Contract

- 返り値は TEXT。`Z` は書式文字列に書いたリテラルで、sqlite が日時を UTC として扱うから正しい。`%z` は sqlite では未対応で、書式に含めると結果全体が `NULL` になる
- 入力に取れるのは ISO 形式のテキスト（`YYYY-MM-DD`、`YYYY-MM-DD HH:MM:SS`、`T` 区切り、`.SSS` の秒未満、末尾の `Z` や `+HH:MM`）、ユリウス日の数値、`'unixepoch'` 修飾子付きの UNIX 秒。`'2024/02/29'` や `'not a date'` は `NULL`（エラーにならない）
- オフセット付きの入力は UTC に変換される（`13:45:07+09:00` → `04:45:07Z`）
- 日付だけの入力は時刻が `00:00:00`。分までの入力（`13:45`）は秒が `00`
- 秒未満は切り捨て（`13:45:07.999` → `13:45:07Z`）。残すなら `%f`（`SS.SSS`）
- `2024-02-30` のような無い日付は正規化されて `2024-03-01` になる（`NULL` にならない）
- `NULL` は `NULL`。`'now'` は UTC の現在時刻
- `'localtime'` 修飾子を付けると実行環境のタイムゾーンに変換される。そのまま `Z` を付けると嘘の表記になる。`'localtime'` の後に `'utc'` を付けると元に戻る
- duckdb: 関数は同名だが引数順が逆で `STRFTIME(ts, '%Y-%m-%dT%H:%M:%SZ')`（1.5 では書式を先にしても通ったが、文書上の順は日時が先）。`ts` は TIMESTAMP / DATE 型が必要で、文字列リテラルも VARCHAR 列もそのまま渡すと Binder Error（1.5 で確認。引数順が両方定義されているため `Could not choose a best candidate function` と候補を絞れずに失敗する。`'...'::TIMESTAMP` / `col::TIMESTAMP` にする）。`%z` は TIMESTAMP で `+00`。無い日付（`2024-02-30`）は Conversion Error。TIMESTAMPTZ は `TimeZone` 設定のローカル時刻で整形されるので、`Z` を付けるなら `ts AT TIME ZONE 'UTC'` で UTC の TIMESTAMP にしてから渡す

## Alternatives

- PostgreSQL: `TO_CHAR(ts AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"')` と書く。MySQL: `DATE_FORMAT(ts, '%Y-%m-%dT%H:%i:%sZ')`（分は `%i`）。BigQuery: `FORMAT_TIMESTAMP('%Y-%m-%dT%H:%M:%SZ', ts, 'UTC')`
- `Z` の代わりに `+00:00` を付けるなら書式を `'%Y-%m-%dT%H:%M:%S+00:00'` にする
- sqlite で `T` 無しの `DATETIME(ts)`（`2024-02-29 13:45:07`）も ISO 8601 として辞書順 = 時系列順で比較できる
- duckdb の `ts::VARCHAR` は `2024-02-29 13:45:07`（`T` も `Z` も無し）。秒未満を残すなら `%g`（ミリ秒）/ `%f`（マイクロ秒）
- 逆変換は sqlite なら `DATETIME(s)`、duckdb なら `s::TIMESTAMP`（末尾 `Z` も受け付ける）

## Pitfalls

- Python の `isoformat()` は naive ならオフセット無し、UTC でも `+00:00`。TypeScript（date-fns の `formatISO`）はローカルオフセット付き。sqlite は常に UTC 扱いで `Z` は自分で書く。3 者で末尾が違うので、受け手の仕様（`Z` 必須か）を確認する
- sqlite の列に型は無いので、保存形式が揃っていないと `STRFTIME` は静かに `NULL` を返す。`'2024/02/29'` のような形式は先に正規化する
- `'localtime'` を付けた値に `Z` を付けない。ローカル表記が要るなら `%z` の無い sqlite ではオフセットを自分で書く
- duckdb の TIMESTAMPTZ は環境の `TimeZone` 設定で表示が変わる。テストと本番で結果が違う原因になるので `AT TIME ZONE 'UTC'` を明示する

## Test

`examples/date-format-iso_test.py`
