# イベント駆動のサーバーレス関数。
# ロググループは Lambda の自動作成に任せず、保持期間付きで先に作る（自動作成だと無期限保持になる）。
# パッケージは Zip（filename）かコンテナイメージ（image_uri）のどちらか一方。

resource "aws_cloudwatch_log_group" "this" {
  name              = "/aws/lambda/${var.function_name}"
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_lambda_function" "this" {
  function_name = var.function_name
  role          = var.role_arn

  package_type     = var.image_uri != null ? "Image" : "Zip"
  filename         = var.filename
  source_code_hash = var.source_code_hash
  image_uri        = var.image_uri
  runtime          = var.runtime
  handler          = var.handler

  timeout                        = var.timeout
  memory_size                    = var.memory_size
  reserved_concurrent_executions = var.reserved_concurrent_executions

  dynamic "environment" {
    for_each = length(var.environment) > 0 ? [var.environment] : []
    content {
      variables = environment.value
    }
  }

  tracing_config {
    mode = var.tracing_mode
  }

  tags = var.tags

  depends_on = [aws_cloudwatch_log_group.this]
}
