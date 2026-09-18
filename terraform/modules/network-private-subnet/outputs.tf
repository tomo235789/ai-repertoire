output "subnet_id" {
  description = "作成したサブネットの ID"
  value       = aws_subnet.this.id
}

output "subnet_arn" {
  description = "作成したサブネットの ARN"
  value       = aws_subnet.this.arn
}

output "route_table_id" {
  description = "サブネットに関連付けた専用ルートテーブルの ID（network-egress-only に渡す）"
  value       = aws_route_table.this.id
}
