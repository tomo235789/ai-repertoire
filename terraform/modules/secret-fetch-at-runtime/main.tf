# 秘密情報を実行時に取得するためのシークレット本体と、それだけを読める最小権限ポリシー。
# 値（aws_secretsmanager_secret_version）は意図的に作らない。Terraform state に平文が残るため、
# 値の投入はコンソール / CLI / ローテーション Lambda など Terraform の外で行う。

locals {
  read_policy_name = coalesce(var.read_policy_name, "${replace(var.name, "/", "-")}-read")

  read_secret_statement = {
    Sid      = "ReadSecretValue"
    Effect   = "Allow"
    Action   = ["secretsmanager:GetSecretValue"]
    Resource = aws_secretsmanager_secret.this.arn
  }

  # 顧客管理キーのときだけ、Secrets Manager 経由の復号を許可する
  decrypt_statement = var.kms_key_arn == null ? [] : [{
    Sid      = "DecryptViaSecretsManager"
    Effect   = "Allow"
    Action   = ["kms:Decrypt"]
    Resource = var.kms_key_arn
    Condition = {
      StringLike = {
        "kms:ViaService" = "secretsmanager.*.amazonaws.com"
      }
    }
  }]
}

resource "aws_secretsmanager_secret" "this" {
  name                    = var.name
  description             = var.description
  kms_key_id              = var.kms_key_arn
  recovery_window_in_days = var.recovery_window_in_days
  tags                    = var.tags
}

resource "aws_iam_policy" "read" {
  name        = local.read_policy_name
  description = "Read the value of secret ${var.name} at runtime"
  policy = jsonencode({
    Version   = "2012-10-17"
    Statement = concat([local.read_secret_statement], local.decrypt_statement)
  })
  tags = var.tags
}
