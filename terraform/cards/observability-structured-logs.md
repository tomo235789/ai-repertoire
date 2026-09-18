---
id: observability-structured-logs
lang: terraform
title: アプリケーションログを構造化して集約する
tags: [CloudWatch Logs, ロググループ, メトリクスフィルタ, 構造化ログ, JSON, エラー集計, グルーイングロバー]
lib: hashicorp/aws
fn: aws_cloudwatch_log_group
since: "5.0"
verified: 2026-09-18
status: public
---

「JSON ログのフィールドごとに CloudWatch メトリクスを抽出したい」という要求に対する設定。ロググループとメトリクスフィルタを 1 module にまとめる。アプリケーションからは `name` 出力を log driver の destination として渡す。

## Signature

```hcl
module "x" { source = "./modules/observability-structured-logs", name, retention_in_days = 30, kms_key_id = null, metric_namespace = null, metric_filters = {}, tags = {} }
-> { id, arn, name, metric_names }
```

## Usage

```hcl
module "app_logs" {
  source = "./modules/observability-structured-logs"
  name             = "/app/example/api"
  retention_in_days = 365
  metric_namespace = "Example/API"
  metric_filters = {
    errors   = { pattern = "{ $.level = \"error\" }", metric_name = "ErrorCount" }
    warnings = { pattern = "{ $.level = \"warn\" }",  metric_name = "WarningCount" }
  }
}
```

## Contract

- ロググループ名は `name` のまま。CloudWatch Logs が許す文字列（英数字と `_ / . # -`、512 文字以内）だけ validation で受ける
- 保持日数: `retention_in_days` は CloudWatch が指定する値のみに限定（0 = 無期限, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653）。間違った値は validation で弾く
- KMS 暗号化: `kms_key_id` が null なら CloudWatch Logs の既定暗号化（AWS 管理キー）、指定すれば BYOK
- メトリクスフィルタ: 各フィルタの `pattern` が JSON ログに一致するたびに `metric_value` を加算。一致がない期間には `default_value` を出力
- メトリクス名は英数字と `_ . / -` のみ、255 文字以内（validation で強制）
- フィルタを渡さない場合、メトリクスフィルタリソースは作成されない
- `tags` はロググループに付く。メトリクスフィルタ自体にはタグが付かない

## Alternatives

- `aws/examples/observability-structured-logs.py`（Boto3 で同じ設定を関数として書く例）
- CloudWatch Logs インサイト — クエリ言語で集計するが、メトリクスへの出力はフィルタが必要
- Datadog / Grafana Loki などの外部ログ収集 — この module は CloudWatch 前提

## Pitfalls

- `retention_in_days` に指定できる値は CloudWatch が定義する一覧に限られる（10 日や 20 日は不可）。30 に丸める必要がある
- メトリクスフィルタのパターンマッチングにはコストがかかる。パターンが多すぎるとログ配信のレイテンシが上がる
- ロググループ名はリージョン間で重複しても OK（CloudWatch Logs はリージョンローカルリソース）。ただし `metric_namespace` のメトリクスは同一リージョンに格納される

## Test

`modules/observability-structured-logs/tests/observability-structured-logs.tftest.hcl`
