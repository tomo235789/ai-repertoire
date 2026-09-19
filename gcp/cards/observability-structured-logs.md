---
id: observability-structured-logs
lang: gcp
title: アプリケーションログを構造化して集約する
tags: [CloudLogging, jsonPayload, ログシンク, 秘匿, cloud-logging, structured-logging, log-sink, redaction]
lib: gcp.logging
fn: log_line
since: "2024"
verified: 2026-09-19
status: public
---

「Cloud Logging が読める形で 1 行ずつ出し、必要なものだけ別の場所へ流す」という要求から、構造化ログとログシンクを組み立てる。時刻は呼び出し側が渡すので関数は純粋。

## Signature

```python
def log_line(timestamp: str, severity: str, message: str, *, trace: str | None = None, fields: dict[str, Any] | None = None) -> str
def log_sink(name: str, destination: str, log_filter: str, *, exclusions: dict[str, str] | None = None, use_partitioned_tables: bool = True) -> dict
```

## Usage

```python
from datetime import datetime, timezone

now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
print(log_line(now, "INFO", "注文を受け付けた", fields={"orderId": "A-1"}))

sink = log_sink("to-bucket", "storage.googleapis.com/example-log-bucket",
                'severity >= "WARNING"')
client.create_sink(parent="projects/my-project", sink=sink)
```

## Contract

- `log_line` は `time` / `severity` / `message` のキーで 1 行の JSON を返す。キーは名前順で、日本語はエスケープしない
- `trace` は `logging.googleapis.com/trace` に入る
- `REDACTED_KEYS` に当たるキーは値が `"[REDACTED]"` になる。入れ子の dict と list の中も辿る
- `RESERVED_KEYS` を `fields` に入れると `ValueError`
- `log_sink` の `exclusions` は除外名順に並び、すべて `disabled: False`
- `bigquery_options` は転送先が BigQuery のときだけ入る
- `ValueError`: タイムスタンプが ISO 8601 でない、未知の重大度、本文が空か 100 KiB 超、1 行が `MAX_ENTRY_BYTES`（200 KiB）を超える、シンク名が空、転送先が `SINK_DESTINATION_FORMS`（バケット・BigQuery データセット・Pub/Sub トピック・プロジェクト・ログバケット）のいずれの形でもない、バケット名や Pub/Sub のトピック ID が命名規則から外れる、フィルタが空
- 同じ入力に同じ出力を返す。現在時刻も乱数も使わない

## Alternatives

- `aws/examples/observability-structured-logs.py` — CloudWatch Logs のロググループ
- `azure/examples/observability-structured-logs.py` — 構造化ログと診断設定
- Cloud Run や GKE では標準出力に出すだけで取り込まれる。エージェントの設定は要らない
- アラートは `observability-alarm-error-rate` で別に組む

## Pitfalls

- 伏せるのはキー名で判断しているだけ。本文に秘密を書いたら消えない
- `severity` を文字列で出さないと全部 DEFAULT になり、重大度で絞れなくなる
- フィルタを空にしたシンクは全ログを流す。転送先の費用が跳ねる
- シンクを作っただけでは書き込めない。返ってくる書き込み用サービスアカウントに転送先の権限を与える
- 除外はシンクではなくログバケット側にも設定できる。二重に除外すると意図せず何も残らないことがある

## Test

`examples/observability-structured-logs_test.py`
