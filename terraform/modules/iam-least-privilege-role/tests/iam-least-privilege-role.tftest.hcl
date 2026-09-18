mock_provider "aws" {
  override_during = plan
  mock_resource "aws_iam_role" {
    defaults = {
      arn = "arn:aws:iam::123456789012:role/example-role"
      id  = "example-role"
    }
  }
}

# 指定したサービスだけが引き受けられ、指定した action / resource だけを許可すること
run "least_privilege" {
  command = plan
  variables {
    name            = "example-role"
    trusted_service = "lambda.amazonaws.com"
    allowed_actions = ["s3:GetObject", "s3:ListBucket"]
    resource_arns   = ["arn:aws:s3:::example-bucket", "arn:aws:s3:::example-bucket/*"]
    tags            = { env = "test" }
  }

  assert {
    condition = alltrue([
      for s in jsondecode(aws_iam_role.this.assume_role_policy).Statement :
      s.Effect == "Allow" && s.Action == "sts:AssumeRole" && s.Principal.Service == "lambda.amazonaws.com"
    ]) && length(jsondecode(aws_iam_role.this.assume_role_policy).Statement) == 1
    error_message = "信頼ポリシーは trusted_service からの sts:AssumeRole だけを許可する"
  }
  assert {
    condition     = length(jsondecode(aws_iam_role_policy.this.policy).Statement) == 1
    error_message = "許可ポリシーの Statement は 1 つ"
  }
  assert {
    condition     = jsondecode(aws_iam_role_policy.this.policy).Statement[0].Effect == "Allow" && tolist(jsondecode(aws_iam_role_policy.this.policy).Statement[0].Action) == tolist(["s3:GetObject", "s3:ListBucket"])
    error_message = "Action は allowed_actions と一致する"
  }
  assert {
    condition     = tolist(jsondecode(aws_iam_role_policy.this.policy).Statement[0].Resource) == tolist(["arn:aws:s3:::example-bucket", "arn:aws:s3:::example-bucket/*"])
    error_message = "Resource は resource_arns と一致する"
  }
  assert {
    condition     = !strcontains(aws_iam_role_policy.this.policy, "\"*\"")
    error_message = "ポリシーに `*` 単独の Action / Resource が無い"
  }
  assert {
    condition     = aws_iam_role.this.permissions_boundary == null && aws_iam_role.this.max_session_duration == 3600
    error_message = "既定は permissions boundary 無し・セッション 1 時間"
  }
  assert {
    condition     = aws_iam_role.this.tags["env"] == "test"
    error_message = "tags がロールに付く"
  }
  assert {
    condition     = output.role_arn == "arn:aws:iam::123456789012:role/example-role" && output.role_name == "example-role" && output.policy_name == "example-role-least-privilege"
    error_message = "outputs はロール ARN・名前・ポリシー名を返す"
  }
}

# permissions boundary とセッション時間を指定できること
run "with_boundary" {
  command = plan
  variables {
    name                     = "example-role"
    trusted_service          = "ecs-tasks.amazonaws.com"
    allowed_actions          = ["sqs:SendMessage"]
    resource_arns            = ["arn:aws:sqs:us-east-1:123456789012:example-queue"]
    permissions_boundary_arn = "arn:aws:iam::123456789012:policy/example-boundary"
    max_session_duration     = 7200
  }

  assert {
    condition     = aws_iam_role.this.permissions_boundary == "arn:aws:iam::123456789012:policy/example-boundary"
    error_message = "permissions boundary が付く"
  }
  assert {
    condition     = aws_iam_role.this.max_session_duration == 7200
    error_message = "max_session_duration が反映される"
  }
}

# Resource に `*` 単独は弾くこと
run "rejects_wildcard_resource" {
  command = plan
  variables {
    name            = "example-role"
    trusted_service = "lambda.amazonaws.com"
    allowed_actions = ["s3:GetObject"]
    resource_arns   = ["*"]
  }
  expect_failures = [var.resource_arns]
}

# Action に `*` 単独は弾くこと
run "rejects_wildcard_action" {
  command = plan
  variables {
    name            = "example-role"
    trusted_service = "lambda.amazonaws.com"
    allowed_actions = ["*"]
    resource_arns   = ["arn:aws:s3:::example-bucket/*"]
  }
  expect_failures = [var.allowed_actions]
}

# サービス全体（s3:*）の許可は弾くこと
run "rejects_service_wide_action" {
  command = plan
  variables {
    name            = "example-role"
    trusted_service = "lambda.amazonaws.com"
    allowed_actions = ["s3:GetObject", "s3:*"]
    resource_arns   = ["arn:aws:s3:::example-bucket/*"]
  }
  expect_failures = [var.allowed_actions]
}

# サービス principal 以外（アカウント ID など）は弾くこと
run "rejects_non_service_principal" {
  command = plan
  variables {
    name            = "example-role"
    trusted_service = "123456789012"
    allowed_actions = ["s3:GetObject"]
    resource_arns   = ["arn:aws:s3:::example-bucket/*"]
  }
  expect_failures = [var.trusted_service]
}

# セッション時間の範囲外は弾くこと
run "rejects_session_duration_out_of_range" {
  command = plan
  variables {
    name                 = "example-role"
    trusted_service      = "lambda.amazonaws.com"
    allowed_actions      = ["s3:GetObject"]
    resource_arns        = ["arn:aws:s3:::example-bucket/*"]
    max_session_duration = 60
  }
  expect_failures = [var.max_session_duration]
}
