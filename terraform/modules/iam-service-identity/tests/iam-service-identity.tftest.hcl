mock_provider "aws" {
  override_during = plan
  mock_resource "aws_iam_role" {
    defaults = {
      arn = "arn:aws:iam::123456789012:role/example-identity"
    }
  }
}

# サービス principal からの sts:AssumeRole だけを許可すること
run "service_principal" {
  command = plan
  variables {
    name              = "example-identity"
    principal_type    = "service"
    service_principal = "ecs-tasks.amazonaws.com"
    policy_arns       = ["arn:aws:iam::123456789012:policy/example-read-only"]
    tags              = { env = "test" }
  }

  assert {
    condition     = length(jsondecode(aws_iam_role.this.assume_role_policy).Statement) == 1
    error_message = "信頼ポリシーの Statement は 1 つ"
  }
  assert {
    condition     = jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Principal.Service == "ecs-tasks.amazonaws.com" && jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Action == "sts:AssumeRole"
    error_message = "サービス principal からの sts:AssumeRole を許可する"
  }
  assert {
    condition     = length(aws_iam_role_policy_attachment.this) == 1 && aws_iam_role_policy_attachment.this["arn:aws:iam::123456789012:policy/example-read-only"].role == "example-identity"
    error_message = "policy_arns の管理ポリシーがロールに付く"
  }
  assert {
    condition     = aws_iam_role.this.tags["env"] == "test" && aws_iam_role.this.max_session_duration == 3600
    error_message = "tags が付き、セッションは既定 1 時間"
  }
  assert {
    condition     = output.role_arn == "arn:aws:iam::123456789012:role/example-identity" && output.role_name == "example-identity" && output.assume_action == "sts:AssumeRole"
    error_message = "outputs はロール ARN・名前・STS アクションを返す"
  }
}

# OIDC では Federated principal と sub / aud の StringEquals 条件が付くこと
run "oidc_principal_exact_subject" {
  command = plan
  variables {
    name              = "example-identity"
    principal_type    = "oidc"
    oidc_provider_arn = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
    oidc_subjects     = ["repo:example-org/example-repo:ref:refs/heads/main"]
  }

  assert {
    condition     = jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Principal.Federated == var.oidc_provider_arn && jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Action == "sts:AssumeRoleWithWebIdentity"
    error_message = "OIDC プロバイダからの sts:AssumeRoleWithWebIdentity を許可する"
  }
  assert {
    condition     = tolist(jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Condition.StringEquals["token.actions.githubusercontent.com:sub"]) == tolist(["repo:example-org/example-repo:ref:refs/heads/main"])
    error_message = "sub は StringEquals で厳密比較する"
  }
  assert {
    condition     = tolist(jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Condition.StringEquals["token.actions.githubusercontent.com:aud"]) == tolist(["sts.amazonaws.com"])
    error_message = "aud は既定で sts.amazonaws.com"
  }
  assert {
    condition     = !can(jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Condition.StringLike)
    error_message = "`*` を含まない sub では StringLike を使わない"
  }
  assert {
    condition     = output.assume_action == "sts:AssumeRoleWithWebIdentity"
    error_message = "assume_action 出力"
  }
}

# sub に `*` を含むときは StringLike、aud は StringEquals のままであること
run "oidc_principal_wildcard_subject" {
  command = plan
  variables {
    name              = "example-identity"
    principal_type    = "oidc"
    oidc_provider_arn = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
    oidc_subjects     = ["repo:example-org/example-repo:*"]
  }

  assert {
    condition     = tolist(jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Condition.StringLike["token.actions.githubusercontent.com:sub"]) == tolist(["repo:example-org/example-repo:*"])
    error_message = "sub は StringLike で比較する"
  }
  assert {
    condition     = tolist(jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Condition.StringEquals["token.actions.githubusercontent.com:aud"]) == tolist(["sts.amazonaws.com"])
    error_message = "aud は StringEquals のまま"
  }
  assert {
    condition     = !can(jsondecode(aws_iam_role.this.assume_role_policy).Statement[0].Condition.StringEquals["token.actions.githubusercontent.com:sub"])
    error_message = "sub は StringEquals 側には入らない"
  }
}

# service なのに service_principal が無い指定は弾くこと
run "rejects_service_without_principal" {
  command = plan
  variables {
    name           = "example-identity"
    principal_type = "service"
  }
  expect_failures = [aws_iam_role.this]
}

# oidc なのに sub の条件が無い指定は弾くこと（プロバイダ全体を信頼してしまう）
run "rejects_oidc_without_subjects" {
  command = plan
  variables {
    name              = "example-identity"
    principal_type    = "oidc"
    oidc_provider_arn = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
  }
  expect_failures = [aws_iam_role.this]
}

# principal_type が service / oidc 以外は弾くこと
run "rejects_unknown_principal_type" {
  command = plan
  variables {
    name           = "example-identity"
    principal_type = "user"
  }
  expect_failures = [var.principal_type]
}

# OIDC プロバイダ以外の ARN は弾くこと
run "rejects_non_oidc_provider_arn" {
  command = plan
  variables {
    name              = "example-identity"
    principal_type    = "oidc"
    oidc_provider_arn = "arn:aws:iam::123456789012:saml-provider/example"
    oidc_subjects     = ["repo:example-org/example-repo:ref:refs/heads/main"]
  }
  expect_failures = [var.oidc_provider_arn]
}
