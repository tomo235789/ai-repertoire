---
id: observability-alarm-error-rate
lang: aws
title: エラー率のしきい値でアラームを発報する
tags: [CloudWatch, アラーム, エラー率, メトリクス数式, 閾値, CloudWatch-alarm, error-rate, metric-expression]
lib: aws.cloudwatch
fn: error_rate_alarm
since: "2024"
verified: 2026-09-18
status: public
---

エラー数 / リクエスト数の割合（%）をしきい値で判定する CloudWatch アラームを、メトリクス数式を使って組み立てる。単一メトリクス形式ではなく `Metrics` 配列の相対数式を使う。

## Signature

```python
def error_rate_alarm(name: str, namespace: str, errors_metric: str, requests_metric: str, dimensions: Mapping[str, str], threshold_percent: float, period: int = 60, evaluation_periods: int = 5, alarm_actions: Sequence[str] = (), *, ok_actions: Sequence[str] = (), datapoints_to_alarm: int | None = None) -> dict[str, Any]
```

## Usage

```python
from observability_alarm_error_rate import error_rate_alarm  # examples/observability-alarm-error-rate.py をコピー

kw = error_rate_alarm(
    "orders-5xx-rate", "AWS/ApiGateway", "5XXError", "Count",
    {"ApiName": "orders", "Stage": "prod"}, threshold_percent=5,
    alarm_actions=[sns_topic_arn],
)
cloudwatch.put_metric_alarm(**kw)  # Metrics[2] の Expression: errors / requests * 100
# TreatMissingData: notBreaching（データ欠落時に発報しない）
```

## Contract

- メトリクス数式 `errors / requests * 100` でエラー率を計算。`Metrics[2].ReturnData=True` のみが可視化用、他は `False`
- `errors_metric` と `requests_metric` は同じ `namespace` に属する。同じ `period`（集計間隔）と `Stat: Sum` で集計
- 両メトリクスは同じ `dimensions` を共有（ディメンションが異なる場合はこの関数では組めない）
- しきい値は 0〜100。bool は受け付けない（float に正規化して返す）
- `period` は 10 / 30 のいずれか、または 60 の倍数。300 秒（5 分）も許可
- `datapoints_to_alarm` 未指定時は `evaluation_periods` と同じ値になる（全期間で超えた場合に発報）
- アラーム通知先は ARN のみ。重複や非 ARN は ValueError
- `TreatMissingData` は `"notBreaching"`（データ欠落時に発報しない）。リクエスト 0 で数式が NaN になっても安全

## Alternatives

- Terraform resource `terraform/cloudwatch_alarm`（同じロジックを HCL で記述。`metric_query` ブロックで `errors / requests * 100` を表現）
- CloudFormation `AWS::CloudWatch::MetricAlarm` の `Metrics` 配列による相対数式

## Pitfalls

- `alarm_actions` / `ok_actions` は ARN 形式に限定。トピック名や URL だとバリデーションで落ちる
- `period` に 45 や 90 などの値は使えない（10/30/60n）。API が即時拒绝する
- シングルメトリクスアラーム（単一メトリクスの Threshold と比較）ではエラー率の計算ができない。必ず `Metrics` 配列の相対数式を使う

## Test

`examples/observability-alarm-error-rate_test.py`
