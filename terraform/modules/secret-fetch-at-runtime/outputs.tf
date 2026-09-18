output "secret_id" {
  description = "シークレットの ID（ARN と同じ）"
  value       = aws_secretsmanager_secret.this.id
}

output "secret_arn" {
  description = "シークレットの ARN。アプリケーションの環境変数や読み取りポリシーの Resource に使う"
  value       = aws_secretsmanager_secret.this.arn
}

output "secret_name" {
  description = "シークレット名"
  value       = aws_secretsmanager_secret.this.name
}

output "read_policy_arn" {
  description = "読み取り用 IAM ポリシーの ARN。実行ロールに aws_iam_role_policy_attachment で付ける"
  value       = aws_iam_policy.read.arn
}

output "read_policy_name" {
  description = "読み取り用 IAM ポリシー名"
  value       = aws_iam_policy.read.name
}
