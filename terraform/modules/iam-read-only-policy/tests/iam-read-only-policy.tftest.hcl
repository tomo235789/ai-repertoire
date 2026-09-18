mock_provider "aws" {
  override_during = plan
  mock_resource "aws_iam_policy" {
    defaults = {
      arn = "arn:aws:iam::123456789012:policy/example-read-only"
    }
  }
}

# 読み取りアクションだけを対象リソースに Allow すること
run "read_only" {
  command = plan
  variables {
    name            = "example-read-only"
    allowed_actions = ["s3:GetObject", "s3:ListBucket", "s3:GetBucketLocation"]
    resource_arns   = ["arn:aws:s3:::example-bucket", "arn:aws:s3:::example-bucket/*"]
    tags            = { env = "test" }
  }

  assert {
    condition     = length(jsondecode(aws_iam_policy.this.policy).Statement) == 1 && jsondecode(aws_iam_policy.this.policy).Statement[0].Effect == "Allow"
    error_message = "Statement は Allow 1 つだけ"
  }
  assert {
    condition     = tolist(jsondecode(aws_iam_policy.this.policy).Statement[0].Action) == tolist(["s3:GetObject", "s3:ListBucket", "s3:GetBucketLocation"])
    error_message = "Action は allowed_actions と一致する"
  }
  assert {
    condition     = tolist(jsondecode(aws_iam_policy.this.policy).Statement[0].Resource) == tolist(["arn:aws:s3:::example-bucket", "arn:aws:s3:::example-bucket/*"])
    error_message = "Resource は resource_arns と一致する"
  }
  assert {
    condition     = !anytrue([for s in jsondecode(aws_iam_policy.this.policy).Statement : s.Effect == "Deny"])
    error_message = "Deny 文は含めない（読み取り以外を許可しないことで足りる）"
  }
  assert {
    condition     = aws_iam_policy.this.tags["env"] == "test" && aws_iam_policy.this.path == "/" && aws_iam_policy.this.description == "Read-only access"
    error_message = "tags が付き、path と description は既定値"
  }
  assert {
    condition     = output.policy_arn == "arn:aws:iam::123456789012:policy/example-read-only" && output.policy_name == "example-read-only" && output.policy_json == aws_iam_policy.this.policy
    error_message = "outputs は ARN・名前・JSON を返す"
  }
}

# Describe* / List* と接頭辞ワイルドカードは受け付け、Resource "*" も許すこと
run "describe_with_wildcard_resource" {
  command = plan
  variables {
    name            = "example-describe"
    allowed_actions = ["ec2:Describe*", "cloudwatch:List*", "logs:GetLogEvents"]
    resource_arns   = ["*"]
  }

  assert {
    condition     = tolist(jsondecode(aws_iam_policy.this.policy).Statement[0].Resource) == tolist(["*"])
    error_message = "リソースレベル権限が無い Describe* のために Resource \"*\" を受け付ける"
  }
}

# 書き込みアクションは弾くこと
run "rejects_write_action" {
  command = plan
  variables {
    name            = "example-read-only"
    allowed_actions = ["s3:GetObject", "s3:PutObject"]
    resource_arns   = ["arn:aws:s3:::example-bucket/*"]
  }
  expect_failures = [var.allowed_actions]
}

# サービス全体（s3:*）や `*` は弾くこと
run "rejects_service_wide_action" {
  command = plan
  variables {
    name            = "example-read-only"
    allowed_actions = ["s3:*"]
    resource_arns   = ["arn:aws:s3:::example-bucket/*"]
  }
  expect_failures = [var.allowed_actions]
}

# 削除系や Decrypt のような読み取りに見えないアクションも弾くこと
run "rejects_delete_and_decrypt" {
  command = plan
  variables {
    name            = "example-read-only"
    allowed_actions = ["s3:DeleteObject", "kms:Decrypt"]
    resource_arns   = ["arn:aws:s3:::example-bucket/*"]
  }
  expect_failures = [var.allowed_actions]
}

# ARN でも "*" でもない Resource は弾くこと
run "rejects_malformed_resource" {
  command = plan
  variables {
    name            = "example-read-only"
    allowed_actions = ["s3:GetObject"]
    resource_arns   = ["example-bucket/*"]
  }
  expect_failures = [var.resource_arns]
}
