output "topic_id" {
  description = "SNS トピックの ID（ARN と同じ）"
  value       = aws_sns_topic.this.id
}

output "topic_arn" {
  description = "SNS トピックの ARN。発行側の sns:Publish の Resource に使う"
  value       = aws_sns_topic.this.arn
}

output "topic_name" {
  description = "SNS トピック名"
  value       = aws_sns_topic.this.name
}

output "queue_ids" {
  description = "キュー名 → キュー URL"
  value       = { for k, q in aws_sqs_queue.subscriber : k => q.id }
}

output "queue_arns" {
  description = "キュー名 → キュー ARN。購読側のロールに sqs:ReceiveMessage / DeleteMessage を許可するときに使う"
  value       = { for k, q in aws_sqs_queue.subscriber : k => q.arn }
}

output "subscription_arns" {
  description = "キュー名 → サブスクリプション ARN"
  value       = { for k, s in aws_sns_topic_subscription.subscriber : k => s.arn }
}
