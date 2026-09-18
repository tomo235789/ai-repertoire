---
id: compute-autoscaling-policy
lang: aws
title: 負荷に応じてインスタンス数を自動調整する
tags: [オートスケーリング, スケーリング, ECS, autoscaling, target tracking, scaling policy, application autoscaling, cpu]
lib: aws.application-autoscaling
fn: ecs_target_tracking
since: "2024"
verified: 2026-09-18
status: public
---

ECS サービスのタスク数を平均 CPU 使用率のターゲット追跡で min〜max の範囲に保つ。出力は boto3 `application-autoscaling` の `register_scalable_target` / `put_scaling_policy` の kwargs。

## Signature

```python
ecs_target_tracking(cluster: str, service: str, min_capacity: int, max_capacity: int, target_cpu_percent: float, scale_in_cooldown: int = 300, scale_out_cooldown: int = 60) -> dict
```

## Usage

```python
from importlib import import_module

ecs_target_tracking = import_module("compute-autoscaling-policy").ecs_target_tracking
cfg = ecs_target_tracking("app-cluster", "api", min_capacity=2, max_capacity=10, target_cpu_percent=60)
# cfg["register_scalable_target"] -> ResourceId "service/app-cluster/api"、ScalableDimension "ecs:service:DesiredCount"
# cfg["put_scaling_policy"]       -> TargetTrackingScaling、ECSServiceAverageCPUUtilization を 60.0 に保つ
# aas.register_scalable_target(**cfg["register_scalable_target"]); aas.put_scaling_policy(**cfg["put_scaling_policy"])
```

## Contract

- 副作用無し。同じ入力から同じ出力。出力は `json.dumps` できる
- `ServiceNamespace: ecs`、`ResourceId: service/<cluster>/<service>`、`ScalableDimension: ecs:service:DesiredCount` が両 API で一致する
- `put_scaling_policy` は `PolicyType: TargetTrackingScaling`、`PredefinedMetricType: ECSServiceAverageCPUUtilization`、`DisableScaleIn: False`、`TargetValue` は float。`PolicyName` は `<service>-cpu-target-tracking`
- `min_capacity` は 0 以上、`max_capacity` は 1 以上、`min_capacity <= max_capacity`。違反は `ValueError`（`min == max` は許可）
- `target_cpu_percent` は 0 より大きく 100 以下。0 や 100 超は `ValueError`
- 既定のクールダウンは scale-in 300 秒 / scale-out 60 秒。負数は `ValueError`。`cluster` / `service` が空なら `ValueError`

## Alternatives

- Terraform: `terraform/modules/compute-autoscaling-policy`（同じ ID。`aws_appautoscaling_target` + `aws_appautoscaling_policy`）
- CloudFormation: `AWS::ApplicationAutoScaling::ScalableTarget` + `ScalingPolicy`
- リクエスト数ベースなら `ALBRequestCountPerTarget`（`ResourceLabel` が要る）、メモリなら `ECSServiceAverageMemoryUtilization`。予測可能な波なら Scheduled Scaling を併用。EC2 Auto Scaling Group は別 API（`autoscaling.put_scaling_policy`）

## Pitfalls

- `register_scalable_target` はサービスが存在しないと失敗する。compute-container-service の `create_service` の後に呼ぶ
- `MinCapacity` / `MaxCapacity` はサービスの `desiredCount` を上書きする。デプロイで `desiredCount` を固定していると綱引きになる
- スケールインは `scale_in_cooldown` の間ずっと目標を下回るまで起きない。短くしすぎるとフラッピング、長すぎるとコスト
- ターゲット追跡は CloudWatch アラームを自動作成・削除する。手で消すと動かなくなる
- `put_scaling_policy` は同名ポリシーを上書きするので再実行に安全。`register_scalable_target` も既存の対象を更新する
- サービスリンクロール `AWSServiceRoleForApplicationAutoScaling_ECSService` は初回に自動作成されるが、SCP で `iam:CreateServiceLinkedRole` を禁じていると失敗する

## Test

`examples/compute-autoscaling-policy_test.py`
