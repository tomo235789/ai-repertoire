output "function_arn" {
  description = "作成した Lambda 関数の ARN"
  value       = aws_lambda_function.this.arn
}

output "function_name" {
  description = "作成した Lambda 関数の名前"
  value       = aws_lambda_function.this.function_name
}

output "invoke_arn" {
  description = "API Gateway などから呼び出すための ARN"
  value       = aws_lambda_function.this.invoke_arn
}

output "log_group_name" {
  description = "関数ログの CloudWatch ロググループ名"
  value       = aws_cloudwatch_log_group.this.name
}
