mock_provider "aws" {}

variables {
  cluster_name = "example"
  service_name = "app"
  min_capacity = 2
  max_capacity = 10
  tags         = { env = "example" }
}

run "cpu_target_tracking" {
  command = plan

  assert {
    condition     = aws_appautoscaling_target.this.resource_id == "service/example/app" && aws_appautoscaling_target.this.service_namespace == "ecs" && aws_appautoscaling_target.this.scalable_dimension == "ecs:service:DesiredCount"
    error_message = "対象は ECS サービスの DesiredCount"
  }
  assert {
    condition     = aws_appautoscaling_target.this.min_capacity == 2 && aws_appautoscaling_target.this.max_capacity == 10
    error_message = "min / max は入力どおり"
  }
  assert {
    condition     = aws_appautoscaling_policy.cpu.policy_type == "TargetTrackingScaling"
    error_message = "ポリシーは Target Tracking"
  }
  assert {
    condition     = aws_appautoscaling_policy.cpu.target_tracking_scaling_policy_configuration[0].predefined_metric_specification[0].predefined_metric_type == "ECSServiceAverageCPUUtilization"
    error_message = "指標はサービス平均 CPU 使用率"
  }
  assert {
    condition     = aws_appautoscaling_policy.cpu.target_tracking_scaling_policy_configuration[0].target_value == 60
    error_message = "目標 CPU 使用率の既定値は 60%"
  }
  assert {
    condition     = aws_appautoscaling_policy.cpu.target_tracking_scaling_policy_configuration[0].scale_out_cooldown == 60 && aws_appautoscaling_policy.cpu.target_tracking_scaling_policy_configuration[0].scale_in_cooldown == 300
    error_message = "クールダウンの既定値はアウト 60 秒 / イン 300 秒"
  }
  assert {
    condition     = aws_appautoscaling_policy.cpu.target_tracking_scaling_policy_configuration[0].disable_scale_in == false
    error_message = "スケールインを無効にしない"
  }
  assert {
    condition     = aws_appautoscaling_policy.cpu.resource_id == aws_appautoscaling_target.this.resource_id && aws_appautoscaling_policy.cpu.scalable_dimension == aws_appautoscaling_target.this.scalable_dimension
    error_message = "ポリシーはターゲットと同じ resource_id / dimension を指す"
  }
  assert {
    condition     = aws_appautoscaling_policy.cpu.name == "app-cpu-target-tracking"
    error_message = "ポリシー名は <service>-cpu-target-tracking"
  }
  assert {
    condition     = aws_appautoscaling_target.this.tags["env"] == "example"
    error_message = "スケーラブルターゲットに tags を付ける"
  }
  assert {
    condition     = output.target_resource_id == "service/example/app" && output.policy_name == "app-cpu-target-tracking"
    error_message = "resource_id とポリシー名を出力する"
  }
}

run "custom_target_and_cooldown" {
  command = plan
  variables {
    target_cpu_utilization = 75
    scale_out_cooldown     = 120
    scale_in_cooldown      = 600
  }

  assert {
    condition     = aws_appautoscaling_policy.cpu.target_tracking_scaling_policy_configuration[0].target_value == 75
    error_message = "目標 CPU 使用率を変えられる"
  }
  assert {
    condition     = aws_appautoscaling_policy.cpu.target_tracking_scaling_policy_configuration[0].scale_out_cooldown == 120 && aws_appautoscaling_policy.cpu.target_tracking_scaling_policy_configuration[0].scale_in_cooldown == 600
    error_message = "クールダウンを変えられる"
  }
}

run "rejects_max_below_min" {
  command = plan
  variables {
    min_capacity = 5
    max_capacity = 4
  }
  expect_failures = [var.max_capacity]
}

run "rejects_cpu_over_100" {
  command = plan
  variables {
    target_cpu_utilization = 101
  }
  expect_failures = [var.target_cpu_utilization]
}

run "rejects_zero_cpu_target" {
  command = plan
  variables {
    target_cpu_utilization = 0
  }
  expect_failures = [var.target_cpu_utilization]
}

run "rejects_cluster_arn" {
  command = plan
  variables {
    cluster_name = "arn:aws:ecs:us-east-1:123456789012:cluster/example"
  }
  expect_failures = [var.cluster_name]
}

run "rejects_negative_cooldown" {
  command = plan
  variables {
    scale_in_cooldown = -1
  }
  expect_failures = [var.scale_in_cooldown]
}
