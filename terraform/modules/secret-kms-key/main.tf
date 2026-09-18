# 顧客管理の対称 KMS キーと別名。年次の自動ローテーションを固定で有効にする。
# キーポリシーは「ルート（任意）」「管理者」「利用者」の 3 種の principal を分けて最小化する。

locals {
  root_statement = var.allow_root_full_access ? [{
    Sid       = "EnableRootAccess"
    Effect    = "Allow"
    Principal = { AWS = "arn:${var.partition}:iam::${var.account_id}:root" }
    Action    = "kms:*"
    Resource  = "*"
  }] : []

  admin_statement = length(var.admin_principal_arns) == 0 ? [] : [{
    Sid       = "AllowKeyAdministration"
    Effect    = "Allow"
    Principal = { AWS = var.admin_principal_arns }
    Action = [
      "kms:Create*",
      "kms:Describe*",
      "kms:Enable*",
      "kms:List*",
      "kms:Put*",
      "kms:Update*",
      "kms:Revoke*",
      "kms:Disable*",
      "kms:Get*",
      "kms:Delete*",
      "kms:TagResource",
      "kms:UntagResource",
      "kms:ScheduleKeyDeletion",
      "kms:CancelKeyDeletion",
    ]
    Resource = "*"
  }]

  user_statement = length(var.user_principal_arns) == 0 ? [] : [{
    Sid       = "AllowKeyUse"
    Effect    = "Allow"
    Principal = { AWS = var.user_principal_arns }
    Action = [
      "kms:Encrypt",
      "kms:Decrypt",
      "kms:ReEncrypt*",
      "kms:GenerateDataKey*",
      "kms:DescribeKey",
    ]
    Resource = "*"
  }]
}

resource "aws_kms_key" "this" {
  description             = var.description
  key_usage               = "ENCRYPT_DECRYPT"
  enable_key_rotation     = true
  deletion_window_in_days = var.deletion_window_in_days
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = concat(local.root_statement, local.admin_statement, local.user_statement)
  })
  tags = var.tags

  lifecycle {
    # ルートも管理者もいないキーは誰もポリシーを直せず、事実上使えなくなる
    precondition {
      condition     = var.allow_root_full_access || length(var.admin_principal_arns) > 0
      error_message = "allow_root_full_access = false のときは admin_principal_arns を 1 つ以上指定する。"
    }
  }
}

resource "aws_kms_alias" "this" {
  name          = var.alias_name
  target_key_id = aws_kms_key.this.key_id
}
