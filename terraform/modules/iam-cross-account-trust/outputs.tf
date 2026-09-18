output "role_arn" {
  description = "ロールの ARN。引き受け側の provider の assume_role.role_arn や sts assume-role --role-arn に渡す"
  value       = aws_iam_role.this.arn
}

output "role_name" {
  description = "ロール名"
  value       = aws_iam_role.this.name
}

output "requires_external_id" {
  description = "引き受けに ExternalId が必須か（常に true）"
  value       = true
}
