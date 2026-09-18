---
id: compute-autoscaling-policy
lang: terraform
title: 負荷に応じてインスタンス数を自動調整する
tags: [オートスケーリング, 自動調整, CPU 使用率, autoscaling, target-tracking, ecs-service, cooldown]
lib: hashicorp/aws
fn: aws_appautoscaling_policy
since: "5.0"
verified: 2026-09-18
status: public
---

ECS サービスのタスク数を、平均 CPU 使用率の目標値に追従する Target Tracking で `min_capacity`〜`max_capacity` の範囲に自動調整する。

## Signature

```hcl
variables: cluster_name, service_name, min_capacity, max_capacity, target_cpu_utilization = 60, scale_out_cooldown = 60, scale_in_cooldown = 300, tags = {}
outputs:   policy_arn, policy_name, target_resource_id
```

## Usage

```hcl
module "app_scaling" {
  source                 = "./modules/compute-autoscaling-policy"
  cluster_name           = "example"
  service_name           = module.app.service_name
  min_capacity           = 2
  max_capacity           = 10
  target_cpu_utilization = 60
}
```

## Contract

- スケーラブルターゲットは `service/<cluster_name>/<service_name>` の `ecs:service:DesiredCount`。`aws_appautoscaling_target` と `aws_appautoscaling_policy` を 1 つずつ作る
- `policy_type = "TargetTrackingScaling"`、指標は `ECSServiceAverageCPUUtilization`、目標値は `target_cpu_utilization`（既定 60%）
- `max_capacity < min_capacity` は validation で拒否。`target_cpu_utilization` は 0 より大きく 100 以下、クールダウンは 0 以上のみ
- クールダウンの既定はスケールアウト 60 秒 / スケールイン 300 秒。スケールインは無効化しない（`disable_scale_in = false`）
- `cluster_name` / `service_name` は名前のみ。ARN は validation で拒否（`resource_id` の形式が壊れるため）
- ポリシー名は `<service_name>-cpu-target-tracking`
- `tags` はスケーラブルターゲットに付ける。`aws_appautoscaling_policy` はタグを持たない

## Alternatives

- メモリやリクエスト数で調整するなら `predefined_metric_type` を `ECSServiceAverageMemoryUtilization` / `ALBRequestCountPerTarget` に変えたポリシーを追加する。同じターゲットに複数ポリシーを付けられる
- 段階的に増減させたいなら `StepScaling`。ただし Target Tracking の方が調整パラメータが少なく、まず選ぶべき
- 決まった時刻に増減させるなら `aws_appautoscaling_scheduled_action`

## Pitfalls

- `resource_id`（クラスタ名・サービス名）の変更はターゲットとポリシーの再作成になる
- compute-container-service の `desired_count` は、オートスケーリングが動き始めると Terraform の値と実際の値がずれて plan に差分が出る。サービス側で `lifecycle { ignore_changes = [desired_count] }` を付ける
- スケールインのクールダウンを短くすると、負荷の谷でタスクが急減して次の山に間に合わない。既定の 300 秒より短くするときは要検証
- `target_cpu_utilization` を高くしすぎる（90% 以上）とスケールアウトが遅れる。サービスの起動時間を考えて余裕を持たせる

## Test

`modules/compute-autoscaling-policy/tests/compute-autoscaling-policy.tftest.hcl`
