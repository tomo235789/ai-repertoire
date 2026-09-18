output "bucket_name" {
  description = "規則を付けたバケット名"
  value       = aws_s3_bucket_lifecycle_configuration.this.bucket
}

output "rule_id" {
  description = "作成した規則の ID"
  value       = var.rule_id
}

output "rule_status" {
  description = "規則の状態（常に Enabled）"
  value       = aws_s3_bucket_lifecycle_configuration.this.rule[0].status
}
