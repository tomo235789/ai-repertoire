output "role_arn" {
  description = "ロールの ARN（ECS の task_role_arn、GitHub Actions の role-to-assume などに渡す）"
  value       = aws_iam_role.this.arn
}

output "role_name" {
  description = "ロール名"
  value       = aws_iam_role.this.name
}

output "assume_action" {
  description = "引き受けに使う STS アクション（sts:AssumeRole か sts:AssumeRoleWithWebIdentity）"
  value       = local.is_oidc ? "sts:AssumeRoleWithWebIdentity" : "sts:AssumeRole"
}
