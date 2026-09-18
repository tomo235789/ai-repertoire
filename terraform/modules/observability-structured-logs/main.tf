# アプリケーションの JSON ログを集約するロググループと、そこからメトリクスを切り出すフィルタ。
resource "aws_cloudwatch_log_group" "this" {
  name              = var.name
  retention_in_days = var.retention_in_days
  kms_key_id        = var.kms_key_id
  tags              = var.tags
}

# JSON ログのフィールドでカウントする（例: { $.level = "error" } → ErrorCount）。
# フィルタは 1 件ごとに metric_value を加算し、一致が無い期間には default_value を出す。
resource "aws_cloudwatch_log_metric_filter" "this" {
  for_each = var.metric_filters

  name           = each.key
  log_group_name = aws_cloudwatch_log_group.this.name
  pattern        = each.value.pattern

  metric_transformation {
    name          = each.value.metric_name
    namespace     = var.metric_namespace
    value         = each.value.metric_value
    default_value = each.value.default_value
  }
}
