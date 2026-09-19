---
id: observability-structured-logs
lang: azure
title: アプリケーションログを構造化して集約する
tags: [構造化ログ, 診断設定, LogAnalytics, 秘匿, structured-logs, diagnostic-settings, log-analytics, redaction]
lib: azure.monitor
fn: log_line
since: "2024"
verified: 2026-09-19
status: public
---

「検索できる形でログを出し、まとめて 1 か所に集める」という要求から、1 行の JSON ログと診断設定を組み立てる。時刻は呼び出し側が渡すので関数は純粋。

## Signature

```python
def log_line(timestamp: str, severity: str, message: str, *, operation_id: str | None = None, fields: dict[str, Any] | None = None) -> str
def diagnostic_setting(workspace_id: str, log_categories, *, metrics: bool = True) -> dict
```

## Usage

```python
from datetime import datetime, timezone

now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
print(log_line(now, "Information", "注文を受け付けた", fields={"orderId": "A-1"}))

cfg = diagnostic_setting(workspace_id, ["AppServiceHTTPLogs"])
client.diagnostic_settings.create_or_update(resource_id, "to-law", cfg)
```

## Contract

- `log_line` は改行を含まない 1 行の JSON を返す。キーは名前順で、日本語はエスケープしない
- `REDACTED_KEYS` に当たるキー（大文字小文字は問わない）は値が `"[REDACTED]"` になる。入れ子の dict と list の中も辿る
- `operation_id` は渡したときだけ `operationId` として入る
- `diagnostic_setting` の `logAnalyticsDestinationType` は常に `"Dedicated"`
- カテゴリは重複を除いて名前順に並ぶ
- 保持期間は診断設定では決まらないので `retentionPolicy` を出さない。ワークスペースかテーブルの設定で決める
- `ValueError`: タイムスタンプが ISO 8601 でない、重大度が既定の 5 つ以外、本文が空か 32 KiB 超、`RESERVED_KEYS` を `fields` に入れた、ワークスペースが `/subscriptions/<id>/resourceGroups/<rg>/providers/...` の形でない、カテゴリが空
- 同じ入力に同じ出力を返す。現在時刻も乱数も使わない

## Alternatives

- `aws/examples/observability-structured-logs.py` — CloudWatch Logs のロググループとメトリックフィルタ
- `gcp/examples/observability-structured-logs.py` — Cloud Logging の構造化ペイロード
- SDK に任せるなら `opentelemetry` のログエクスポーターを使い、整形は自前で持たない
- 監視の発報は `observability-alarm-error-rate` で別に組む

## Pitfalls

- 伏せるのはキー名で判断しているだけ。本文に秘密を書いたら消えない。`message` には値を埋めない
- 診断設定の保持日数は廃止された。保持はワークスペースかテーブル単位で決める
- `AzureDiagnostics` テーブルは全リソース共通で列数の上限がある。専用テーブルにしないと列が溢れて欠ける
- Log Analytics の取り込みには数分の遅れがある。直後に検索しても出てこない
- 1 レコードの上限を超える長い本文は切り捨てられる。長い内容はストレージに置いて参照だけ載せる

## Test

`examples/observability-structured-logs_test.py`
