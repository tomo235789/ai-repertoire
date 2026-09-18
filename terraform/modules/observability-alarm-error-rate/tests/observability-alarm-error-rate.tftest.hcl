mock_provider "aws" {}

variables {
  alarm_name          = "example-api-error-rate"
  namespace           = "AWS/ApplicationELB"
  error_metric_name   = "HTTPCode_Target_5XX_Count"
  request_metric_name = "RequestCount"
  dimensions          = { LoadBalancer = "app/example/0123456789abcdef" }
  alarm_actions       = ["arn:aws:sns:us-east-1:123456789012:example-alerts"]
  tags                = { env = "example" }
}

run "error_rate_alarm" {
  command = plan
  assert {
    condition     = [for q in aws_cloudwatch_metric_alarm.this.metric_query : q.expression if q.id == "error_rate"][0] == "errors / requests * 100"
    error_message = "エラー率は errors / requests * 100 の metric math"
  }
  assert {
    condition     = [for q in aws_cloudwatch_metric_alarm.this.metric_query : q.return_data if q.id == "error_rate"][0] == true && alltrue([for q in aws_cloudwatch_metric_alarm.this.metric_query : q.return_data == false if q.id != "error_rate"])
    error_message = "判定に使うのは error_rate だけ（元メトリクスは return_data = false）"
  }
  assert {
    condition     = alltrue([for q in aws_cloudwatch_metric_alarm.this.metric_query : one(q.metric).stat == "Sum" && one(q.metric).period == 60 && one(q.metric).namespace == "AWS/ApplicationELB" if q.id != "error_rate"])
    error_message = "分子・分母は同じ名前空間・期間の Sum"
  }
  assert {
    condition     = alltrue([for q in aws_cloudwatch_metric_alarm.this.metric_query : one(q.metric).dimensions == tomap({ LoadBalancer = "app/example/0123456789abcdef" }) if q.id != "error_rate"])
    error_message = "ディメンションは両メトリクスに同じものが付く"
  }
  assert {
    condition     = [for q in aws_cloudwatch_metric_alarm.this.metric_query : one(q.metric).metric_name if q.id == "errors"][0] == "HTTPCode_Target_5XX_Count" && [for q in aws_cloudwatch_metric_alarm.this.metric_query : one(q.metric).metric_name if q.id == "requests"][0] == "RequestCount"
    error_message = "errors / requests がそれぞれ variable のメトリクスを指す"
  }
  assert {
    condition     = aws_cloudwatch_metric_alarm.this.treat_missing_data == "notBreaching"
    error_message = "データ欠損（分母 0 を含む）は notBreaching"
  }
  assert {
    condition     = aws_cloudwatch_metric_alarm.this.comparison_operator == "GreaterThanThreshold" && aws_cloudwatch_metric_alarm.this.threshold == 5 && aws_cloudwatch_metric_alarm.this.evaluation_periods == 5
    error_message = "既定は 5% 超を 5 期間連続で判定"
  }
  assert {
    condition     = aws_cloudwatch_metric_alarm.this.alarm_actions == toset(["arn:aws:sns:us-east-1:123456789012:example-alerts"]) && length(aws_cloudwatch_metric_alarm.this.ok_actions) == 0
    error_message = "ALARM 時は SNS に通知、OK 通知は既定で無し"
  }
  assert {
    condition     = aws_cloudwatch_metric_alarm.this.tags == tomap({ env = "example" })
    error_message = "tags がリソースに付く"
  }
}

run "m_of_n_with_ok_actions" {
  command = plan
  variables {
    threshold_percent   = 1.5
    period              = 300
    evaluation_periods  = 3
    datapoints_to_alarm = 2
    ok_actions          = ["arn:aws:sns:us-east-1:123456789012:example-alerts"]
  }
  assert {
    condition     = aws_cloudwatch_metric_alarm.this.threshold == 1.5 && aws_cloudwatch_metric_alarm.this.datapoints_to_alarm == 2 && aws_cloudwatch_metric_alarm.this.evaluation_periods == 3
    error_message = "M of N（3 期間中 2 期間）としきい値の小数を受け付ける"
  }
  assert {
    condition     = alltrue([for q in aws_cloudwatch_metric_alarm.this.metric_query : one(q.metric).period == 300 if q.id != "error_rate"])
    error_message = "period は両メトリクスに反映される"
  }
  assert {
    condition     = length(aws_cloudwatch_metric_alarm.this.ok_actions) == 1
    error_message = "ok_actions を渡せば復旧通知が付く"
  }
}

run "rejects_threshold_over_100" {
  command = plan
  variables {
    threshold_percent = 101
  }
  expect_failures = [var.threshold_percent]
}

run "rejects_period_not_multiple_of_60" {
  command = plan
  variables {
    period = 90
  }
  expect_failures = [var.period]
}

run "rejects_datapoints_over_evaluation_periods" {
  command = plan
  variables {
    evaluation_periods  = 3
    datapoints_to_alarm = 4
  }
  expect_failures = [var.datapoints_to_alarm]
}

run "rejects_non_sns_alarm_action" {
  command = plan
  variables {
    alarm_actions = ["arn:aws:lambda:us-east-1:123456789012:function:example"]
  }
  expect_failures = [var.alarm_actions]
}
