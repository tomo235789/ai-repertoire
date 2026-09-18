# 順序保証（FIFO）と、処理に失敗し続けたメッセージを退避する DLQ の組。
# 両方とも保存時暗号化（SSE-SQS か顧客管理 KMS）を必ず有効にする。

locals {
  dlq_name = coalesce(var.dlq_name, "${trimsuffix(var.name, ".fifo")}-dlq.fifo")
  use_cmk  = var.kms_key_id != null
}

resource "aws_sqs_queue" "dlq" {
  name                        = local.dlq_name
  fifo_queue                  = true
  content_based_deduplication = var.content_based_deduplication
  message_retention_seconds   = var.dlq_message_retention_seconds

  sqs_managed_sse_enabled           = local.use_cmk ? null : true
  kms_master_key_id                 = var.kms_key_id
  kms_data_key_reuse_period_seconds = local.use_cmk ? var.kms_data_key_reuse_period_seconds : null

  tags = var.tags

  lifecycle {
    precondition {
      condition     = var.dlq_message_retention_seconds >= var.message_retention_seconds
      error_message = "dlq_message_retention_seconds は message_retention_seconds 以上にする。"
    }
  }
}

resource "aws_sqs_queue" "this" {
  name                        = var.name
  fifo_queue                  = true
  content_based_deduplication = var.content_based_deduplication
  deduplication_scope         = var.high_throughput ? "messageGroup" : "queue"
  fifo_throughput_limit       = var.high_throughput ? "perMessageGroupId" : "perQueue"
  visibility_timeout_seconds  = var.visibility_timeout_seconds
  message_retention_seconds   = var.message_retention_seconds

  sqs_managed_sse_enabled           = local.use_cmk ? null : true
  kms_master_key_id                 = var.kms_key_id
  kms_data_key_reuse_period_seconds = local.use_cmk ? var.kms_data_key_reuse_period_seconds : null

  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn
    maxReceiveCount     = var.max_receive_count
  })

  tags = var.tags
}

# DLQ 側で「このキューからだけ」退避を受け付ける（別リソースにして循環参照を避ける）
resource "aws_sqs_queue_redrive_allow_policy" "dlq" {
  queue_url = aws_sqs_queue.dlq.id
  redrive_allow_policy = jsonencode({
    redrivePermission = "byQueue"
    sourceQueueArns   = [aws_sqs_queue.this.arn]
  })
}
