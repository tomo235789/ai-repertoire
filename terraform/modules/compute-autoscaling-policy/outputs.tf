output "policy_arn" {
  description = "作成したスケーリングポリシーの ARN"
  value       = aws_appautoscaling_policy.cpu.arn
}

output "policy_name" {
  description = "作成したスケーリングポリシーの名前"
  value       = aws_appautoscaling_policy.cpu.name
}

output "target_resource_id" {
  description = "スケーラブルターゲットの resource_id（service/<cluster>/<service>）"
  value       = aws_appautoscaling_target.this.resource_id
}
