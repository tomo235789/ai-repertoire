output "endpoint_id" {
  description = "作成した VPC エンドポイントの ID"
  value       = aws_vpc_endpoint.this.id
}

output "endpoint_arn" {
  description = "作成した VPC エンドポイントの ARN"
  value       = aws_vpc_endpoint.this.arn
}

output "dns_entries" {
  description = "Interface 型のエンドポイントの DNS 名（private_dns_enabled = false のとき SDK に渡す）"
  value       = aws_vpc_endpoint.this.dns_entry
}
