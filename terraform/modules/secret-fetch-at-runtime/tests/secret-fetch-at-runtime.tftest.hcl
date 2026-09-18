mock_provider "aws" {
  override_during = plan
  mock_resource "aws_secretsmanager_secret" {
    defaults = {
      arn = "arn:aws:secretsmanager:us-east-1:123456789012:secret:example/app/db-AbCdEf"
    }
  }
}

variables {
  name = "example/app/db"
  tags = { env = "example" }
}

run "secret_without_value" {
  command = plan
  assert {
    condition     = aws_secretsmanager_secret.this.name == "example/app/db"
    error_message = "secret name must echo var.name"
  }
  assert {
    condition     = aws_secretsmanager_secret.this.kms_key_id == null
    error_message = "default must use the AWS managed key (kms_key_id null)"
  }
  assert {
    condition     = aws_secretsmanager_secret.this.recovery_window_in_days == 30
    error_message = "default recovery window must be 30 days"
  }
  assert {
    condition     = aws_secretsmanager_secret.this.tags["env"] == "example" && aws_iam_policy.read.tags["env"] == "example"
    error_message = "tags must be applied to the secret and the policy"
  }
}

run "read_policy_is_least_privilege" {
  command = plan
  assert {
    condition     = length(jsondecode(aws_iam_policy.read.policy).Statement) == 1
    error_message = "without a customer key the policy must have exactly one statement"
  }
  assert {
    condition     = jsondecode(aws_iam_policy.read.policy).Statement[0].Action == ["secretsmanager:GetSecretValue"]
    error_message = "only secretsmanager:GetSecretValue must be allowed"
  }
  assert {
    condition     = jsondecode(aws_iam_policy.read.policy).Statement[0].Resource == "arn:aws:secretsmanager:us-east-1:123456789012:secret:example/app/db-AbCdEf"
    error_message = "the resource must be the secret ARN, never a wildcard"
  }
  assert {
    condition     = aws_iam_policy.read.name == "example-app-db-read"
    error_message = "default policy name must be derived from the secret name"
  }
}

run "customer_key_adds_scoped_decrypt" {
  command = plan
  variables {
    kms_key_arn = "arn:aws:kms:us-east-1:123456789012:key/11111111-2222-3333-4444-555555555555"
  }
  assert {
    condition     = aws_secretsmanager_secret.this.kms_key_id == "arn:aws:kms:us-east-1:123456789012:key/11111111-2222-3333-4444-555555555555"
    error_message = "the secret must be encrypted with the given key"
  }
  assert {
    condition     = length(jsondecode(aws_iam_policy.read.policy).Statement) == 2
    error_message = "a customer key must add exactly one decrypt statement"
  }
  assert {
    condition     = jsondecode(aws_iam_policy.read.policy).Statement[1].Action == ["kms:Decrypt"] && jsondecode(aws_iam_policy.read.policy).Statement[1].Resource == var.kms_key_arn
    error_message = "decrypt must be limited to the given key"
  }
  assert {
    condition     = jsondecode(aws_iam_policy.read.policy).Statement[1].Condition.StringLike["kms:ViaService"] == "secretsmanager.*.amazonaws.com"
    error_message = "decrypt must only be allowed via Secrets Manager"
  }
}

run "rejects_immediate_deletion" {
  command = plan
  variables {
    recovery_window_in_days = 0
  }
  expect_failures = [var.recovery_window_in_days]
}

run "rejects_key_alias" {
  command = plan
  variables {
    kms_key_arn = "alias/example"
  }
  expect_failures = [var.kms_key_arn]
}

run "rejects_invalid_name" {
  command = plan
  variables {
    name = "bad name with spaces"
  }
  expect_failures = [var.name]
}
