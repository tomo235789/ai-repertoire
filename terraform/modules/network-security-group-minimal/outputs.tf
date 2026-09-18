output "security_group_id" {
  description = "作成したセキュリティグループの ID"
  value       = aws_security_group.this.id
}

output "security_group_arn" {
  description = "作成したセキュリティグループの ARN"
  value       = aws_security_group.this.arn
}

output "security_group_name" {
  description = "作成したセキュリティグループの名前"
  value       = aws_security_group.this.name
}
