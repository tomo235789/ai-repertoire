output "distribution_id" {
  description = "CloudFront ディストリビューションの ID"
  value       = aws_cloudfront_distribution.this.id
}

output "distribution_arn" {
  description = "CloudFront ディストリビューションの ARN（バケットポリシーの条件に使う）"
  value       = aws_cloudfront_distribution.this.arn
}

output "domain_name" {
  description = "CloudFront が払い出すドメイン名（DNS の別名レコードの向き先）"
  value       = aws_cloudfront_distribution.this.domain_name
}

output "origin_access_control_id" {
  description = "作成した OAC の ID"
  value       = aws_cloudfront_origin_access_control.this.id
}
