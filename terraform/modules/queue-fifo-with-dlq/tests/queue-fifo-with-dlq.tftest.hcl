mock_provider "aws" {}

override_resource {
  target          = aws_sqs_queue.this
  override_during = plan
  values = {
    arn = "arn:aws:sqs:us-east-1:123456789012:example-orders.fifo"
  }
}

override_resource {
  target          = aws_sqs_queue.dlq
  override_during = plan
  values = {
    arn = "arn:aws:sqs:us-east-1:123456789012:example-orders-dlq.fifo"
  }
}

variables {
  name = "example-orders.fifo"
  tags = { env = "example" }
}

run "fifo_pair_defaults" {
  command = plan
  assert {
    condition     = aws_sqs_queue.this.fifo_queue == true && aws_sqs_queue.dlq.fifo_queue == true
    error_message = "both queues must be FIFO"
  }
  assert {
    condition     = aws_sqs_queue.this.name == "example-orders.fifo" && aws_sqs_queue.dlq.name == "example-orders-dlq.fifo"
    error_message = "the DLQ name must be derived from the queue name"
  }
  assert {
    condition     = aws_sqs_queue.this.content_based_deduplication == false && aws_sqs_queue.this.deduplication_scope == "queue" && aws_sqs_queue.this.fifo_throughput_limit == "perQueue"
    error_message = "defaults must be explicit deduplication ids and per-queue throughput"
  }
  assert {
    condition     = aws_sqs_queue.this.visibility_timeout_seconds == 30
    error_message = "default visibility timeout must be 30 seconds"
  }
  assert {
    condition     = aws_sqs_queue.this.message_retention_seconds == 345600 && aws_sqs_queue.dlq.message_retention_seconds == 1209600
    error_message = "defaults must keep messages 4 days in the queue and 14 days in the DLQ"
  }
  assert {
    condition     = aws_sqs_queue.this.tags["env"] == "example" && aws_sqs_queue.dlq.tags["env"] == "example"
    error_message = "tags must be applied to both queues"
  }
}

run "encryption_defaults_to_sse_sqs" {
  command = plan
  assert {
    condition     = aws_sqs_queue.this.sqs_managed_sse_enabled == true && aws_sqs_queue.dlq.sqs_managed_sse_enabled == true
    error_message = "without a customer key both queues must use SSE-SQS"
  }
  assert {
    condition     = aws_sqs_queue.this.kms_master_key_id == null && aws_sqs_queue.dlq.kms_master_key_id == null
    error_message = "without a customer key kms_master_key_id must be unset"
  }
}

run "redrive_targets_the_dlq" {
  command = plan
  variables {
    max_receive_count = 3
  }
  assert {
    condition     = jsondecode(aws_sqs_queue.this.redrive_policy).deadLetterTargetArn == "arn:aws:sqs:us-east-1:123456789012:example-orders-dlq.fifo"
    error_message = "redrive must point at the DLQ"
  }
  assert {
    condition     = jsondecode(aws_sqs_queue.this.redrive_policy).maxReceiveCount == 3
    error_message = "maxReceiveCount must follow the variable"
  }
  assert {
    condition     = jsondecode(aws_sqs_queue_redrive_allow_policy.dlq.redrive_allow_policy).redrivePermission == "byQueue"
    error_message = "the DLQ must only accept redrive from named queues"
  }
  assert {
    condition     = jsondecode(aws_sqs_queue_redrive_allow_policy.dlq.redrive_allow_policy).sourceQueueArns == ["arn:aws:sqs:us-east-1:123456789012:example-orders.fifo"]
    error_message = "the DLQ must only accept redrive from the main queue"
  }
}

run "customer_key_and_high_throughput" {
  command = plan
  variables {
    kms_key_id                  = "alias/example/app"
    content_based_deduplication = true
    high_throughput             = true
    dlq_name                    = "example-orders-failed.fifo"
  }
  assert {
    condition     = aws_sqs_queue.this.kms_master_key_id == "alias/example/app" && aws_sqs_queue.dlq.kms_master_key_id == "alias/example/app"
    error_message = "both queues must use the customer key"
  }
  assert {
    condition     = aws_sqs_queue.this.kms_data_key_reuse_period_seconds == 300
    error_message = "data key reuse period must be set with a customer key"
  }
  assert {
    condition     = aws_sqs_queue.this.content_based_deduplication == true && aws_sqs_queue.this.deduplication_scope == "messageGroup" && aws_sqs_queue.this.fifo_throughput_limit == "perMessageGroupId"
    error_message = "high throughput mode must switch scope and limit to message group"
  }
  assert {
    condition     = aws_sqs_queue.dlq.name == "example-orders-failed.fifo"
    error_message = "dlq_name must override the derived name"
  }
}

run "rejects_name_without_fifo_suffix" {
  command = plan
  variables {
    name = "example-orders"
  }
  expect_failures = [var.name]
}

run "rejects_dlq_name_without_fifo_suffix" {
  command = plan
  variables {
    dlq_name = "example-orders-dlq"
  }
  expect_failures = [var.dlq_name]
}

run "rejects_zero_receive_count" {
  command = plan
  variables {
    max_receive_count = 0
  }
  expect_failures = [var.max_receive_count]
}

run "rejects_dlq_retention_shorter_than_queue" {
  command = plan
  variables {
    message_retention_seconds     = 1209600
    dlq_message_retention_seconds = 345600
  }
  expect_failures = [aws_sqs_queue.dlq]
}
