mock_provider "aws" {}

variables {
  name             = "/app/example/api"
  metric_namespace = "Example/App"
  metric_filters = {
    errors = { pattern = "{ $.level = \"error\" }", metric_name = "ErrorCount" }
  }
  tags = { env = "example" }
}

run "log_group_with_error_filter" {
  command = plan
  variables {
    kms_key_id = "arn:aws:kms:us-east-1:123456789012:key/11111111-2222-3333-4444-555555555555"
  }
  assert {
    condition     = aws_cloudwatch_log_group.this.name == "/app/example/api" && output.name == "/app/example/api"
    error_message = "ロググループ名は variable のとおり"
  }
  assert {
    condition     = aws_cloudwatch_log_group.this.retention_in_days == 30
    error_message = "既定の保持は 30 日"
  }
  assert {
    condition     = aws_cloudwatch_log_group.this.kms_key_id == var.kms_key_id
    error_message = "KMS キーで暗号化される"
  }
  assert {
    condition     = aws_cloudwatch_log_metric_filter.this["errors"].pattern == "{ $.level = \"error\" }"
    error_message = "フィルタパターンは variable のとおり"
  }
  assert {
    condition     = aws_cloudwatch_log_metric_filter.this["errors"].log_group_name == "/app/example/api"
    error_message = "フィルタは同じロググループに付く"
  }
  assert {
    condition     = one(aws_cloudwatch_log_metric_filter.this["errors"].metric_transformation).name == "ErrorCount" && one(aws_cloudwatch_log_metric_filter.this["errors"].metric_transformation).namespace == "Example/App"
    error_message = "メトリクス名と名前空間は variable のとおり"
  }
  assert {
    condition     = one(aws_cloudwatch_log_metric_filter.this["errors"].metric_transformation).value == "1" && one(aws_cloudwatch_log_metric_filter.this["errors"].metric_transformation).default_value == "0"
    error_message = "1 件ごとに 1 を加算し、一致が無い期間は 0 を出す"
  }
  assert {
    condition     = output.metric_names == { errors = "ErrorCount" }
    error_message = "metric_names はフィルタ名 → メトリクス名"
  }
  assert {
    condition     = aws_cloudwatch_log_group.this.tags == tomap({ env = "example" })
    error_message = "tags がロググループに付く"
  }
}

run "no_filters_and_aws_managed_encryption" {
  command = plan
  variables {
    metric_filters    = {}
    retention_in_days = 3653
  }
  assert {
    condition     = length(aws_cloudwatch_log_metric_filter.this) == 0
    error_message = "metric_filters が空ならフィルタを作らない"
  }
  assert {
    condition     = aws_cloudwatch_log_group.this.retention_in_days == 3653 && var.kms_key_id == null
    error_message = "許可された保持日数はそのまま通り、KMS は省略できる"
  }
}

run "rejects_unsupported_retention" {
  command = plan
  variables {
    retention_in_days = 10
  }
  expect_failures = [var.retention_in_days]
}

run "rejects_non_arn_kms_key" {
  command = plan
  variables {
    kms_key_id = "alias/example"
  }
  expect_failures = [var.kms_key_id]
}

run "rejects_invalid_metric_name" {
  command = plan
  variables {
    metric_filters = {
      errors = { pattern = "{ $.level = \"error\" }", metric_name = "Error Count" }
    }
  }
  expect_failures = [var.metric_filters]
}
