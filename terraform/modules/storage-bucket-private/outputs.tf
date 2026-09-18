output "bucket_name" {
  description = "バケット名"
  value       = aws_s3_bucket.this.bucket
}

output "bucket_arn" {
  description = "バケットの ARN（IAM ポリシーの Resource に使う）"
  value       = aws_s3_bucket.this.arn
}

output "bucket_id" {
  description = "バケット ID（他の aws_s3_bucket_* リソースの bucket 引数に渡す）"
  value       = aws_s3_bucket.this.id
}

output "sse_algorithm" {
  description = "既定の保存時暗号化方式（AES256 か aws:kms）"
  value       = local.use_kms ? "aws:kms" : "AES256"
}
