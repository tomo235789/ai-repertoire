# 1 つの SNS トピックから複数の SQS キューへファンアウトする。
# 各キューのポリシーは「このトピックからの sqs:SendMessage」だけを許可する。

locals {
  use_cmk = var.kms_key_id != null
  queues  = toset(var.queue_names)
}

resource "aws_sns_topic" "this" {
  name              = var.topic_name
  kms_master_key_id = var.kms_key_id
  tags              = var.tags
}

resource "aws_sqs_queue" "subscriber" {
  for_each = local.queues

  name                       = each.value
  visibility_timeout_seconds = var.visibility_timeout_seconds
  message_retention_seconds  = var.message_retention_seconds

  sqs_managed_sse_enabled = local.use_cmk ? null : true
  kms_master_key_id       = var.kms_key_id

  tags = var.tags
}

resource "aws_sqs_queue_policy" "subscriber" {
  for_each = local.queues

  queue_url = aws_sqs_queue.subscriber[each.key].id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowSendFromTopic"
      Effect    = "Allow"
      Principal = { Service = "sns.amazonaws.com" }
      Action    = ["sqs:SendMessage"]
      Resource  = aws_sqs_queue.subscriber[each.key].arn
      Condition = {
        ArnEquals = {
          "aws:SourceArn" = aws_sns_topic.this.arn
        }
      }
    }]
  })
}

resource "aws_sns_topic_subscription" "subscriber" {
  for_each = local.queues

  topic_arn            = aws_sns_topic.this.arn
  protocol             = "sqs"
  endpoint             = aws_sqs_queue.subscriber[each.key].arn
  raw_message_delivery = var.raw_message_delivery

  depends_on = [aws_sqs_queue_policy.subscriber]
}
