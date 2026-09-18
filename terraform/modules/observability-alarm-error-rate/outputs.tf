output "id" {
  description = "アラームの ID（= アラーム名）"
  value       = aws_cloudwatch_metric_alarm.this.id
}

output "arn" {
  description = "アラームの ARN"
  value       = aws_cloudwatch_metric_alarm.this.arn
}

output "name" {
  description = "アラーム名"
  value       = aws_cloudwatch_metric_alarm.this.alarm_name
}
