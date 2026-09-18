output "id" {
  description = "DB インスタンスの識別子"
  value       = aws_db_instance.this.id
}

output "arn" {
  description = "DB インスタンスの ARN"
  value       = aws_db_instance.this.arn
}

output "address" {
  description = "接続ホスト名"
  value       = aws_db_instance.this.address
}

output "port" {
  description = "接続ポート"
  value       = aws_db_instance.this.port
}

output "master_user_secret_arn" {
  description = "マスターパスワードを保管する Secrets Manager シークレットの ARN"
  value       = one(aws_db_instance.this.master_user_secret[*].secret_arn)
}
