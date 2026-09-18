output "service_id" {
  description = "作成した ECS サービスの ID（ARN）"
  value       = aws_ecs_service.this.id
}

output "service_name" {
  description = "作成した ECS サービスの名前（compute-autoscaling-policy に渡す）"
  value       = aws_ecs_service.this.name
}

output "task_definition_arn" {
  description = "作成したタスク定義の ARN（リビジョン付き）"
  value       = aws_ecs_task_definition.this.arn
}

output "log_group_name" {
  description = "コンテナログの CloudWatch ロググループ名"
  value       = aws_cloudwatch_log_group.this.name
}
