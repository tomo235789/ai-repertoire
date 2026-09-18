mock_provider "aws" {}

variables {
  alias_name = "alias/example/app"
  account_id = "123456789012"
  tags       = { env = "example" }
}

run "key_defaults" {
  command = plan
  assert {
    condition     = aws_kms_key.this.enable_key_rotation == true
    error_message = "automatic key rotation must always be enabled"
  }
  assert {
    condition     = aws_kms_key.this.key_usage == "ENCRYPT_DECRYPT"
    error_message = "the key must be a symmetric encryption key"
  }
  assert {
    condition     = aws_kms_key.this.deletion_window_in_days == 30
    error_message = "default deletion window must be 30 days"
  }
  assert {
    condition     = aws_kms_alias.this.name == "alias/example/app"
    error_message = "alias must echo alias_name"
  }
  assert {
    condition     = aws_kms_key.this.tags["env"] == "example"
    error_message = "tags must be applied to the key"
  }
}

run "root_only_policy" {
  command = plan
  assert {
    condition     = length(jsondecode(aws_kms_key.this.policy).Statement) == 1
    error_message = "with no admins or users the policy must contain only the root statement"
  }
  assert {
    condition     = jsondecode(aws_kms_key.this.policy).Statement[0].Principal.AWS == "arn:aws:iam::123456789012:root"
    error_message = "root statement must target the account root"
  }
  assert {
    condition     = jsondecode(aws_kms_key.this.policy).Statement[0].Action == "kms:*"
    error_message = "root statement must grant kms:*"
  }
}

run "admins_and_users_are_separated" {
  command = plan
  variables {
    allow_root_full_access  = false
    admin_principal_arns    = ["arn:aws:iam::123456789012:role/example-key-admin"]
    user_principal_arns     = ["arn:aws:iam::123456789012:role/example-app"]
    deletion_window_in_days = 7
  }
  assert {
    condition     = length(jsondecode(aws_kms_key.this.policy).Statement) == 2
    error_message = "without root there must be exactly the admin and user statements"
  }
  assert {
    condition     = jsondecode(aws_kms_key.this.policy).Statement[0].Sid == "AllowKeyAdministration" && jsondecode(aws_kms_key.this.policy).Statement[0].Principal.AWS == ["arn:aws:iam::123456789012:role/example-key-admin"]
    error_message = "admin statement must target the admin principals"
  }
  assert {
    condition     = !contains(jsondecode(aws_kms_key.this.policy).Statement[0].Action, "kms:Decrypt") && !contains(jsondecode(aws_kms_key.this.policy).Statement[0].Action, "kms:Encrypt")
    error_message = "admins must not be able to encrypt or decrypt"
  }
  assert {
    condition     = jsondecode(aws_kms_key.this.policy).Statement[1].Sid == "AllowKeyUse" && jsondecode(aws_kms_key.this.policy).Statement[1].Principal.AWS == ["arn:aws:iam::123456789012:role/example-app"]
    error_message = "user statement must target the user principals"
  }
  assert {
    condition     = !contains(jsondecode(aws_kms_key.this.policy).Statement[1].Action, "kms:PutKeyPolicy") && !contains(jsondecode(aws_kms_key.this.policy).Statement[1].Action, "kms:ScheduleKeyDeletion")
    error_message = "users must not be able to administer the key"
  }
  assert {
    condition     = aws_kms_key.this.deletion_window_in_days == 7
    error_message = "deletion window must follow the variable"
  }
}

run "rejects_key_nobody_can_manage" {
  command = plan
  variables {
    allow_root_full_access = false
  }
  expect_failures = [aws_kms_key.this]
}

run "rejects_alias_without_prefix" {
  command = plan
  variables {
    alias_name = "example/app"
  }
  expect_failures = [var.alias_name]
}

run "rejects_reserved_alias" {
  command = plan
  variables {
    alias_name = "alias/aws/example"
  }
  expect_failures = [var.alias_name]
}

run "rejects_short_deletion_window" {
  command = plan
  variables {
    deletion_window_in_days = 3
  }
  expect_failures = [var.deletion_window_in_days]
}

run "rejects_invalid_account_id" {
  command = plan
  variables {
    account_id = "12345"
  }
  expect_failures = [var.account_id]
}
