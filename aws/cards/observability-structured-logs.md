---
id: observability-structured-logs
lang: aws
title: アプリケーションログを構造化して集約する
tags: [CloudWatch, ログ, 構造化, メトリクスフィルター, JSON, CloudWatch-logs, structured-logs, metric-filter]
lib: aws.logs
fn: log_group_with_error_metric
since: "2024"
verified: 2026-09-18
status: public
---

JSON 構造化ログのロググループ作成・保持期間設定・エラー行を数えるメトリクスフィルターの 3 つの CloudWatch Logs の kwargs を 1 回の呼び出しで組み立てる。出力は `create_log_group` / `put_retention_policy` / `put_metric_filter` の 3 キー。

## Signature

```python
def log_group_with_error_metric(name: str, retention_days: int, kms_key_id: str | None = None, error_pattern: str = DEFAULT_ERROR_PATTERN, metric_namespace: str = "Application", *, metric_name: str = "ErrorCount", tags: Mapping[str, str] | None = None) -> dict[str, Any]
```

## Usage

```python
from observability_structured_logs import log_group_with_error_metric  # examples/observability-structured-logs.py をコピー

kw = log_group_with_error_metric("/app/api", 30, kms_key_id=KEY, tags={"env": "prod"})
logs.create_log_group(**kw["create_log_group"])                        # CREATE → STANDARD クラス
logs.put_retention_policy(**kw["put_retention_policy"])                # 30 日に保持
logs.put_metric_filter(**kw["put_metric_filter"])                      # JSON の level=error を数える
# メトリクス名空間 "Application" に "ErrorCount"（Count）として集計される
```

## Contract

- `create_log_group` は `logGroupClass: STANDARD`。`kms_key_id` 有りで `kmsKeyId` を含める
- `put_retention_policy` の `retentionInDays` は許容値のいずれか（1, 3, 5, 7, 14, 30, ..., 3653）。それ以外は ValueError
- `put_metric_filter` は JSON の `{ $.level = "error" }` を既定パターンにする。一致時にメトリクス値 `1`、非一致時は `defaultValue: 0.0`
- 3 つの kwargs すべてが同じロググループ名を指す
- `metric_namespace` は空でなく `AWS/` で始まらない名前（カスタム名前空間）。既定は `"Application"`
- `tags` はキー順にソートして格納。`kms_key_id` は鍵 ARN のみ（エイリアスや鍵 ID は拒否）
- 同じ入力に同じ出力を返し、全体を `json.dumps` できる

## Alternatives

- Terraform resource `terraform/log_group` / `terraform/metric_filter`（同じロジックを HCL で記述）
- CloudFormation `AWS::Logs::LogGroup` / `AWS::Logs::MetricFilter` リソース。3 つのリソースを並べる

## Pitfalls

- CloudWatch Logs の kinesis は lowerCamelCase。Terraform の snake_case と違うので混同しない（`kmsKeyId` / `retentionInDays`）
- CloudWatch Logs の KMS 暗号化はエイリアスや鍵 ID を受け付けない。必須で鍵 ARN（`arn:aws:kms:...:key/...`）を渡す
- リテンション日数は固定の選択肢のみ。31 日や 100 日などの値は使えない
- メトリクスフィルターのフィルタパターンが空文字列だと「全行に一致」してすべてのログ行数がエラーとして計上される

## Test

`examples/observability-structured-logs_test.py`
