output "bucket_name" {
  description = "バージョニングを有効にしたバケット名。storage-bucket-lifecycle の bucket_name に渡して非現行バージョンの削除規則を併用する"
  value       = aws_s3_bucket_versioning.this.bucket
}

output "versioning_status" {
  description = "バージョニングの状態（常に Enabled）"
  value       = one(aws_s3_bucket_versioning.this.versioning_configuration).status
}

output "mfa_delete_enabled" {
  description = "MFA Delete が有効か"
  value       = var.mfa_delete
}

output "noncurrent_versions_retained_forever" {
  description = "この module だけでは非現行バージョンが無期限に残る（常に true）。storage-bucket-lifecycle の noncurrent_version_expiration_days で保持期間を決める"
  value       = true
}
