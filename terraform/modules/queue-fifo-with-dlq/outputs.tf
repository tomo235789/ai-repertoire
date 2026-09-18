output "queue_id" {
  description = "メインキューの URL（SDK の QueueUrl）"
  value       = aws_sqs_queue.this.id
}

output "queue_arn" {
  description = "メインキューの ARN"
  value       = aws_sqs_queue.this.arn
}

output "queue_name" {
  description = "メインキュー名"
  value       = aws_sqs_queue.this.name
}

output "dlq_id" {
  description = "DLQ の URL"
  value       = aws_sqs_queue.dlq.id
}

output "dlq_arn" {
  description = "DLQ の ARN"
  value       = aws_sqs_queue.dlq.arn
}

output "dlq_name" {
  description = "DLQ 名"
  value       = aws_sqs_queue.dlq.name
}
