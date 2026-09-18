output "policy_arn" {
  description = "ポリシーの ARN（aws_iam_role_policy_attachment の policy_arn に渡す）"
  value       = aws_iam_policy.this.arn
}

output "policy_name" {
  description = "ポリシー名"
  value       = aws_iam_policy.this.name
}

output "policy_json" {
  description = "ポリシー本文の JSON（レビューやスナップショット比較に使う）"
  value       = aws_iam_policy.this.policy
}
