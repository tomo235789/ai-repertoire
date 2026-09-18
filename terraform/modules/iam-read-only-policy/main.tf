# 読み取り専用のアクセスポリシー（顧客管理ポリシー）。
# Get* / List* / Describe* 系のアクションだけを Allow し、書き込み系は variable の validation で弾く。

locals {
  policy = {
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ReadOnly"
        Effect   = "Allow"
        Action   = var.allowed_actions
        Resource = var.resource_arns
      },
    ]
  }
}

resource "aws_iam_policy" "this" {
  name        = var.name
  path        = var.path
  description = var.description
  policy      = jsonencode(local.policy)
  tags        = var.tags
}
