---
id: observability-alarm-error-rate
lang: terraform
title: エラー率のしきい値でアラームを発報する
tags: [CloudWatch アラーム, エラー率, metric math, SNS 通知, M of N, シーディングロジック, 復旧通知]
lib: hashicorp/aws
fn: aws_cloudwatch_metric_alarm
since: "5.0"
verified: 2026-09-18
status: public
---

「`errors / requests * 100` のエラー率を metric math で計算し、閾値超えで SNS に通知する」CloudWatch アラーム。分母が 0 の期間（データ欠損）には誤発報しないように `notBreaching` を指定している。

## Signature

```hcl
module "x" { source = "./modules/observability-alarm-error-rate", alarm_name, namespace, error_metric_name, request_metric_name, dimensions = {}, period = 60, threshold_percent = 5, evaluation_periods = 5, datapoints_to_alarm = null, alarm_actions, ok_actions = [], tags = {} }
-> { id, arn, name }
```

## Usage

```hcl
module "elb_error_alarm" {
  source              = "./modules/observability-alarm-error-rate"
  alarm_name          = "app-elb-5xx-error-rate"
  namespace           = "AWS/ApplicationELB"
  error_metric_name   = "HTTPCode_Target_5XX_Count"
  request_metric_name = "RequestCount"
  dimensions          = { LoadBalancer = "app/example/0123456789abcdef" }
  threshold_percent   = 1.5  # エラー率 1.5% 超で発報
  alarm_actions       = ["arn:aws:sns:us-east-1:123456789012:alerts"]
}
```

## Contract

- エラー率の計算式: `metric_query` の 3 つめのクエリで `errors / requests * 100` を計算。元メトリクス（errors / requests）は `return_data = false` で判定に使わない
- データ欠損処理: `treat_missing_data = "notBreaching"`。分母が 0 の期間も「しきい値未満」として扱い、誤発報しない
- しきい値: `threshold_percent` を超えたとき ALARM 状態（`GreaterThanThreshold`）
- M of N: `datapoints_to_alarm` で `evaluation_periods` のうち何期間超過すれば発報するかを決める。null なら全期間一致が必要
- 通知: `alarm_actions` は必須（SNS トピック ARN を 1 つ以上）。`ok_actions` は省略可能（指定すると復旧通知も出る）
- period: 60 の倍数（秒）。分母が 0 でもデータ点が生成されないため `default_value = 0` で補完するメトリクスフィルタと組み合わせると安定する
- 両メトリクスの `namespace` / `period` / `dimensions` は共通。別々の設定は受け付けない
- `alarm_actions` に SNS 以外の ARN（Lambda など）を渡すと validation で弾く

## Alternatives

- `aws/examples/observability-alarm-error-rate.py`（Boto3 で同じ設定を関数として書く例）
- CloudWatch Synthetics — エンドツーエンドのチェックだが、エラー率のアラートには向かない
- 単一メトリクスアラーム（`aws_cloudwatch_metric_alarm` で `metric_name` のみ）— 「5XX 絶対数」ならこちらで十分。この module は「比率」に特化している

## Pitfalls

- `threshold_percent = 0` は validation で弾く（0% より大きい必要がある）。しかし実質的に全期間発報することになる
- `treat_missing_data` を `breaching` にすると、データ欠損時にアラームが発報する（負荷ゼロのときに誤検知の原因になる）
- `datapoints_to_alarm` が null の場合、デフォルトは `evaluation_periods` と同じ（全期間を超過）＝最も厳しい判定になる
- SNS トピック ARN 以外を `alarm_actions` に渡すと validation で弾く。Lambda や SQS を使いたいときは SNS トピック経由でサブスクライブする

## Test

`modules/observability-alarm-error-rate/tests/observability-alarm-error-rate.tftest.hcl`
