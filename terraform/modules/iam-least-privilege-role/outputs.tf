output "role_arn" {
  description = "ロールの ARN（Lambda の role、ECS の task_role_arn などに渡す）"
  value       = aws_iam_role.this.arn
}

output "role_name" {
  description = "ロール名"
  value       = aws_iam_role.this.name
}

output "policy_name" {
  description = "ロールに付けたインラインポリシー名"
  value       = aws_iam_role_policy.this.name
}
