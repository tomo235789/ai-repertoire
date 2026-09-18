# 別アカウントからの引き受けを許可する信頼関係。
# 指定した principal からだけ、必ず ExternalId 付きで引き受けられるロールを作る。

locals {
  condition = merge(
    { StringEquals = { "sts:ExternalId" = var.external_id } },
    var.require_mfa ? { Bool = { "aws:MultiFactorAuthPresent" = "true" } } : {},
  )

  assume_role_policy = {
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCrossAccountAssume"
        Effect    = "Allow"
        Principal = { AWS = var.trusted_principal_arns }
        Action    = "sts:AssumeRole"
        Condition = local.condition
      },
    ]
  }
}

resource "aws_iam_role" "this" {
  name                 = var.name
  assume_role_policy   = jsonencode(local.assume_role_policy)
  max_session_duration = var.max_session_duration
  tags                 = var.tags
}

resource "aws_iam_role_policy_attachment" "this" {
  for_each   = toset(var.policy_arns)
  role       = aws_iam_role.this.name
  policy_arn = each.value
}
