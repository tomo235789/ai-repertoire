output "id" {
  description = "ロググループの ID"
  value       = aws_cloudwatch_log_group.this.id
}

output "arn" {
  description = "ロググループの ARN"
  value       = aws_cloudwatch_log_group.this.arn
}

output "name" {
  description = "ロググループ名（アプリケーションのログドライバに渡す）"
  value       = aws_cloudwatch_log_group.this.name
}

output "metric_names" {
  description = "フィルタ名 → 出力メトリクス名"
  value       = { for k, f in var.metric_filters : k => f.metric_name }
}
