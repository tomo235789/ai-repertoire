mock_provider "aws" {
  override_during = plan
  mock_resource "aws_iam_role" {
    defaults = {
      arn = "arn:aws:iam::123456789012:role/example-cross-account"
    }
  }
}

# 指定した別アカウントの principal から ExternalId 付きでだけ引き受けられること
run "cross_account_with_external_id" {
  command = plan
  variables {
    name                   = "example-cross-account"
    trusted_principal_arns = ["arn:aws:iam::210987654321:root"]
    external_id            = "example-external-id"
    policy_arns            = ["arn:aws:iam::123456789012:policy/example-read-only"]
    tags                   = { env = "test" }
  }

  assert {
    condition     = length(jsondecode(aws_iam_role.this.assume_role_policy).Statement) == 1
    error_message = "信頼ポリシーの Statement は 1 つ"
  }
  assert {
    condition     = tolist(jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Principal.AWS) == tolist(["arn:aws:iam::210987654321:root"]) && jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Action == "sts:AssumeRole"
    error_message = "trusted_principal_arns からの sts:AssumeRole を許可する"
  }
  assert {
    condition     = jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Condition.StringEquals["sts:ExternalId"] == "example-external-id"
    error_message = "sts:ExternalId の StringEquals 条件が必ず付く"
  }
  assert {
    condition     = !can(jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Condition.Bool)
    error_message = "require_mfa 既定 false では MFA 条件を付けない"
  }
  assert {
    condition     = length(aws_iam_role_policy_attachment.this) == 1 && aws_iam_role_policy_attachment.this["arn:aws:iam::123456789012:policy/example-read-only"].role == "example-cross-account"
    error_message = "policy_arns の管理ポリシーがロールに付く"
  }
  assert {
    condition     = aws_iam_role.this.tags["env"] == "test" && aws_iam_role.this.max_session_duration == 3600
    error_message = "tags が付き、セッションは既定 1 時間"
  }
  assert {
    condition     = output.role_arn == "arn:aws:iam::123456789012:role/example-cross-account" && output.role_name == "example-cross-account" && output.requires_external_id == true
    error_message = "outputs はロール ARN・名前・ExternalId 必須を返す"
  }
}

# MFA 必須と複数 principal・長いセッションを指定できること
run "with_mfa_and_multiple_principals" {
  command = plan
  variables {
    name                   = "example-cross-account"
    trusted_principal_arns = ["arn:aws:iam::210987654321:role/deployer", "arn:aws:iam::210987654321:user/alice"]
    external_id            = "example-external-id"
    require_mfa            = true
    max_session_duration   = 14400
  }

  assert {
    condition     = jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Condition.Bool["aws:MultiFactorAuthPresent"] == "true"
    error_message = "require_mfa = true で MFA 条件が付く"
  }
  assert {
    condition     = jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Condition.StringEquals["sts:ExternalId"] == "example-external-id"
    error_message = "MFA を付けても ExternalId 条件は残る"
  }
  assert {
    condition     = length(jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Principal.AWS) == 2
    error_message = "複数 principal を許可できる"
  }
  assert {
    condition     = aws_iam_role.this.max_session_duration == 14400
    error_message = "max_session_duration が反映される"
  }
}

# ExternalId が空のときは弾くこと
run "rejects_empty_external_id" {
  command = plan
  variables {
    name                   = "example-cross-account"
    trusted_principal_arns = ["arn:aws:iam::210987654321:root"]
    external_id            = ""
  }
  expect_failures = [var.external_id]
}

# ExternalId に `*` は弾くこと
run "rejects_wildcard_external_id" {
  command = plan
  variables {
    name                   = "example-cross-account"
    trusted_principal_arns = ["arn:aws:iam::210987654321:root"]
    external_id            = "*"
  }
  expect_failures = [var.external_id]
}

# principal に `*` は弾くこと
run "rejects_wildcard_principal" {
  command = plan
  variables {
    name                   = "example-cross-account"
    trusted_principal_arns = ["*"]
    external_id            = "example-external-id"
  }
  expect_failures = [var.trusted_principal_arns]
}

# アカウント ID だけ（ARN でない）や 12 桁でない ID は弾くこと
run "rejects_bare_account_id" {
  command = plan
  variables {
    name                   = "example-cross-account"
    trusted_principal_arns = ["210987654321", "arn:aws:iam::12345:root"]
    external_id            = "example-external-id"
  }
  expect_failures = [var.trusted_principal_arns]
}

# セッション時間の範囲外は弾くこと
run "rejects_session_duration_out_of_range" {
  command = plan
  variables {
    name                   = "example-cross-account"
    trusted_principal_arns = ["arn:aws:iam::210987654321:root"]
    external_id            = "example-external-id"
    max_session_duration   = 86400
  }
  expect_failures = [var.max_session_duration]
}
