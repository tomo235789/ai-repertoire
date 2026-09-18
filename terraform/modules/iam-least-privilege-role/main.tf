# 特定の操作だけを許可する最小権限のロール。
# 信頼する AWS サービスからだけ引き受けられ、明示した action と resource 以外は何も許可しない。

locals {
  assume_role_policy = {
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowServiceAssume"
        Effect    = "Allow"
        Principal = { Service = var.trusted_service }
        Action    = "sts:AssumeRole"
      },
    ]
  }

  permissions_policy = {
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "LeastPrivilege"
        Effect   = "Allow"
        Action   = var.allowed_actions
        Resource = var.resource_arns
      },
    ]
  }
}

resource "aws_iam_role" "this" {
  name                 = var.name
  assume_role_policy   = jsonencode(local.assume_role_policy)
  permissions_boundary = var.permissions_boundary_arn
  max_session_duration = var.max_session_duration
  tags                 = var.tags
}

# インラインポリシーにするとロールと寿命が一致し、他のロールに使い回されない
resource "aws_iam_role_policy" "this" {
  name   = "${var.name}-least-privilege"
  role   = aws_iam_role.this.id
  policy = jsonencode(local.permissions_policy)
}
