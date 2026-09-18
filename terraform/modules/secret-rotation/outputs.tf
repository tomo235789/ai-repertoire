output "id" {
  description = "ローテーション設定の ID（対象シークレットの ARN と同じ）"
  value       = aws_secretsmanager_secret_rotation.this.id
}

output "secret_arn" {
  description = "ローテーション対象のシークレット ARN"
  value       = aws_secretsmanager_secret_rotation.this.secret_id
}

output "rotation_lambda_arn" {
  description = "ローテーションを実行する Lambda 関数の ARN"
  value       = aws_secretsmanager_secret_rotation.this.rotation_lambda_arn
}
