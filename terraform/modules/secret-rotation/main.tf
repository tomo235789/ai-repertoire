# 既存シークレットに定期ローテーションを設定する。
# ローテーション Lambda 本体・その実行ロール・Secrets Manager からの Invoke 許可は module の外で用意する。
# aws_secretsmanager_secret_rotation はタグを持たない。

resource "aws_secretsmanager_secret_rotation" "this" {
  secret_id           = var.secret_arn
  rotation_lambda_arn = var.rotation_lambda_arn
  rotate_immediately  = var.rotate_immediately

  rotation_rules {
    automatically_after_days = var.rotation_days
  }
}
