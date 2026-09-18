mock_provider "aws" {}

variables {
  secret_arn          = "arn:aws:secretsmanager:us-east-1:123456789012:secret:example/app/db-AbCdEf"
  rotation_lambda_arn = "arn:aws:lambda:us-east-1:123456789012:function:example-rotate-db"
}

run "rotation_defaults" {
  command = plan
  assert {
    condition     = aws_secretsmanager_secret_rotation.this.secret_id == var.secret_arn
    error_message = "rotation must target the given secret"
  }
  assert {
    condition     = aws_secretsmanager_secret_rotation.this.rotation_lambda_arn == var.rotation_lambda_arn
    error_message = "rotation must use the given lambda"
  }
  assert {
    condition     = aws_secretsmanager_secret_rotation.this.rotation_rules[0].automatically_after_days == 30
    error_message = "default interval must be 30 days"
  }
  assert {
    condition     = aws_secretsmanager_secret_rotation.this.rotate_immediately == true
    error_message = "default must rotate immediately after apply"
  }
  assert {
    condition     = output.secret_arn == var.secret_arn && output.rotation_lambda_arn == var.rotation_lambda_arn
    error_message = "outputs must echo the inputs"
  }
}

run "custom_interval_without_immediate_rotation" {
  command = plan
  variables {
    rotation_days      = 90
    rotate_immediately = false
  }
  assert {
    condition     = aws_secretsmanager_secret_rotation.this.rotation_rules[0].automatically_after_days == 90
    error_message = "interval must follow rotation_days"
  }
  assert {
    condition     = aws_secretsmanager_secret_rotation.this.rotate_immediately == false
    error_message = "rotate_immediately must be configurable"
  }
}

run "rejects_zero_days" {
  command = plan
  variables {
    rotation_days = 0
  }
  expect_failures = [var.rotation_days]
}

run "rejects_secret_name_instead_of_arn" {
  command = plan
  variables {
    secret_arn = "example/app/db"
  }
  expect_failures = [var.secret_arn]
}

run "rejects_lambda_name_instead_of_arn" {
  command = plan
  variables {
    rotation_lambda_arn = "example-rotate-db"
  }
  expect_failures = [var.rotation_lambda_arn]
}
