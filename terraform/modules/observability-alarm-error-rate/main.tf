# エラー率 = errors / requests * 100 を metric math で計算し、しきい値超えで SNS に通知するアラーム。
resource "aws_cloudwatch_metric_alarm" "this" {
  alarm_name          = var.alarm_name
  alarm_description   = "Error rate (${var.error_metric_name} / ${var.request_metric_name}) exceeds ${var.threshold_percent}%"
  comparison_operator = "GreaterThanThreshold"
  threshold           = var.threshold_percent
  evaluation_periods  = var.evaluation_periods
  datapoints_to_alarm = var.datapoints_to_alarm

  # データが無い期間（リクエスト 0 で分母が 0 → データ点が作られない）は「しきい値未満」として扱い、誤発報しない
  treat_missing_data = "notBreaching"

  metric_query {
    id          = "errors"
    return_data = false
    metric {
      namespace   = var.namespace
      metric_name = var.error_metric_name
      dimensions  = var.dimensions
      period      = var.period
      stat        = "Sum"
    }
  }

  metric_query {
    id          = "requests"
    return_data = false
    metric {
      namespace   = var.namespace
      metric_name = var.request_metric_name
      dimensions  = var.dimensions
      period      = var.period
      stat        = "Sum"
    }
  }

  metric_query {
    id          = "error_rate"
    expression  = "errors / requests * 100"
    label       = "Error rate (%)"
    return_data = true
  }

  alarm_actions = var.alarm_actions
  ok_actions    = var.ok_actions
  tags          = var.tags
}
