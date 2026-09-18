output "id" {
  description = "DB インスタンスの識別子"
  value       = aws_db_instance.this.id
}

output "arn" {
  description = "DB インスタンスの ARN"
  value       = aws_db_instance.this.arn
}

output "backup_retention_period" {
  description = "適用された自動バックアップの保持日数"
  value       = aws_db_instance.this.backup_retention_period
}
