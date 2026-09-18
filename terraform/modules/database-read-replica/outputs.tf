output "id" {
  description = "レプリカの識別子"
  value       = aws_db_instance.this.id
}

output "arn" {
  description = "レプリカの ARN"
  value       = aws_db_instance.this.arn
}

output "address" {
  description = "読み取り用の接続ホスト名"
  value       = aws_db_instance.this.address
}
