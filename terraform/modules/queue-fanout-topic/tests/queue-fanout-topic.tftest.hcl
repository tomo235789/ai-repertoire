mock_provider "aws" {
  override_during = plan
  mock_resource "aws_sqs_queue" {
    defaults = {
      arn = "arn:aws:sqs:us-east-1:123456789012:example-subscriber"
    }
  }
}

override_resource {
  target          = aws_sns_topic.this
  override_during = plan
  values = {
    arn = "arn:aws:sns:us-east-1:123456789012:example-events"
  }
}

variables {
  topic_name  = "example-events"
  queue_names = ["example-billing", "example-notify"]
  tags        = { env = "example" }
}

run "one_topic_many_queues" {
  command = plan
  assert {
    condition     = aws_sns_topic.this.name == "example-events"
    error_message = "topic name must echo topic_name"
  }
  assert {
    condition     = length(aws_sqs_queue.subscriber) == 2 && length(aws_sns_topic_subscription.subscriber) == 2 && length(aws_sqs_queue_policy.subscriber) == 2
    error_message = "there must be one queue, one policy and one subscription per queue name"
  }
  assert {
    condition     = aws_sqs_queue.subscriber["example-billing"].name == "example-billing" && aws_sqs_queue.subscriber["example-notify"].name == "example-notify"
    error_message = "queues must be keyed and named by queue_names"
  }
  assert {
    condition     = alltrue([for s in aws_sns_topic_subscription.subscriber : s.protocol == "sqs" && s.raw_message_delivery == false])
    error_message = "subscriptions must be sqs with the SNS envelope by default"
  }
  assert {
    condition     = alltrue([for s in aws_sns_topic_subscription.subscriber : s.topic_arn == "arn:aws:sns:us-east-1:123456789012:example-events"])
    error_message = "every subscription must belong to the topic"
  }
  assert {
    condition     = aws_sns_topic.this.tags["env"] == "example" && alltrue([for q in aws_sqs_queue.subscriber : q.tags["env"] == "example"])
    error_message = "tags must be applied to the topic and every queue"
  }
}

run "queue_policy_only_allows_this_topic" {
  command = plan
  assert {
    condition     = alltrue([for p in aws_sqs_queue_policy.subscriber : length(jsondecode(p.policy).Statement) == 1])
    error_message = "each queue policy must have exactly one statement"
  }
  assert {
    condition     = alltrue([for p in aws_sqs_queue_policy.subscriber : jsondecode(p.policy).Statement[0].Principal.Service == "sns.amazonaws.com"])
    error_message = "only the SNS service principal may send"
  }
  assert {
    condition     = alltrue([for p in aws_sqs_queue_policy.subscriber : jsondecode(p.policy).Statement[0].Action == ["sqs:SendMessage"]])
    error_message = "only sqs:SendMessage may be allowed"
  }
  assert {
    condition     = alltrue([for p in aws_sqs_queue_policy.subscriber : jsondecode(p.policy).Statement[0].Condition.ArnEquals["aws:SourceArn"] == "arn:aws:sns:us-east-1:123456789012:example-events"])
    error_message = "sending must be limited to this topic via aws:SourceArn"
  }
  assert {
    condition     = alltrue([for p in aws_sqs_queue_policy.subscriber : jsondecode(p.policy).Statement[0].Resource == "arn:aws:sqs:us-east-1:123456789012:example-subscriber"])
    error_message = "the statement resource must be the queue ARN, never a wildcard"
  }
}

run "encryption_defaults_to_sse_sqs" {
  command = plan
  assert {
    condition     = alltrue([for q in aws_sqs_queue.subscriber : q.sqs_managed_sse_enabled == true && q.kms_master_key_id == null])
    error_message = "without a customer key every queue must use SSE-SQS"
  }
  assert {
    condition     = aws_sns_topic.this.kms_master_key_id == null
    error_message = "without a customer key the topic has no kms key"
  }
}

run "customer_key_and_raw_delivery" {
  command = plan
  variables {
    kms_key_id           = "alias/example/app"
    raw_message_delivery = true
  }
  assert {
    condition     = aws_sns_topic.this.kms_master_key_id == "alias/example/app"
    error_message = "the topic must use the customer key"
  }
  assert {
    condition     = alltrue([for q in aws_sqs_queue.subscriber : q.kms_master_key_id == "alias/example/app"])
    error_message = "every queue must use the customer key"
  }
  assert {
    condition     = alltrue([for s in aws_sns_topic_subscription.subscriber : s.raw_message_delivery == true])
    error_message = "raw_message_delivery must be configurable"
  }
}

run "rejects_empty_queue_list" {
  command = plan
  variables {
    queue_names = []
  }
  expect_failures = [var.queue_names]
}

run "rejects_duplicate_queue_names" {
  command = plan
  variables {
    queue_names = ["example-billing", "example-billing"]
  }
  expect_failures = [var.queue_names]
}

run "rejects_fifo_queue_names" {
  command = plan
  variables {
    queue_names = ["example-billing.fifo"]
  }
  expect_failures = [var.queue_names]
}

run "rejects_fifo_topic_name" {
  command = plan
  variables {
    topic_name = "example-events.fifo"
  }
  expect_failures = [var.topic_name]
}
