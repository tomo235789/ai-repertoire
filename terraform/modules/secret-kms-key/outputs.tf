output "key_id" {
  description = "KMS キーの ID"
  value       = aws_kms_key.this.key_id
}

output "key_arn" {
  description = "KMS キーの ARN。他リソースの kms_key_id / kms_master_key_id に渡す"
  value       = aws_kms_key.this.arn
}

output "alias_name" {
  description = "キーの別名（alias/...）"
  value       = aws_kms_alias.this.name
}

output "alias_arn" {
  description = "別名の ARN"
  value       = aws_kms_alias.this.arn
}
