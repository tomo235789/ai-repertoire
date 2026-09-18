mock_provider "aws" {}

variables {
  function_name = "order-events"
  role_arn      = "arn:aws:iam::123456789012:role/order-events"
  tags          = { env = "example" }
}

run "zip_package" {
  command = plan
  variables {
    filename                       = "build/order-events.zip"
    source_code_hash               = "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
    runtime                        = "python3.12"
    handler                        = "app.handler"
    environment                    = { TABLE_NAME = "orders" }
    reserved_concurrent_executions = 10
  }

  assert {
    condition     = aws_lambda_function.this.package_type == "Zip" && aws_lambda_function.this.filename == "build/order-events.zip"
    error_message = "filename を指定したら Zip パッケージ"
  }
  assert {
    condition     = aws_lambda_function.this.runtime == "python3.12" && aws_lambda_function.this.handler == "app.handler"
    error_message = "runtime と handler は入力どおり"
  }
  assert {
    condition     = aws_lambda_function.this.role == "arn:aws:iam::123456789012:role/order-events"
    error_message = "実行ロールは入力どおり"
  }
  assert {
    condition     = aws_lambda_function.this.tracing_config[0].mode == "Active"
    error_message = "既定で X-Ray トレースを Active にする"
  }
  assert {
    condition     = aws_lambda_function.this.reserved_concurrent_executions == 10
    error_message = "予約済み同時実行数は入力どおり"
  }
  assert {
    condition     = aws_lambda_function.this.environment[0].variables["TABLE_NAME"] == "orders"
    error_message = "環境変数を渡す"
  }
  assert {
    condition     = aws_lambda_function.this.timeout == 30 && aws_lambda_function.this.memory_size == 256
    error_message = "timeout / memory_size の既定値は 30 秒 / 256 MB"
  }
  assert {
    condition     = aws_cloudwatch_log_group.this.name == "/aws/lambda/order-events" && aws_cloudwatch_log_group.this.retention_in_days == 30
    error_message = "ロググループは /aws/lambda/<name> に保持期間付き（既定 30 日）で作る"
  }
  assert {
    condition     = aws_lambda_function.this.tags["env"] == "example" && aws_cloudwatch_log_group.this.tags["env"] == "example"
    error_message = "全リソースに tags を付ける"
  }
  assert {
    condition     = output.log_group_name == "/aws/lambda/order-events"
    error_message = "ロググループ名を出力する"
  }
}

run "container_image" {
  command = plan
  variables {
    image_uri    = "123456789012.dkr.ecr.us-east-1.amazonaws.com/order-events:1.2.3"
    tracing_mode = "PassThrough"
  }

  assert {
    condition     = aws_lambda_function.this.package_type == "Image" && aws_lambda_function.this.image_uri == "123456789012.dkr.ecr.us-east-1.amazonaws.com/order-events:1.2.3"
    error_message = "image_uri を指定したらコンテナイメージ"
  }
  assert {
    condition     = aws_lambda_function.this.filename == null && aws_lambda_function.this.runtime == null && aws_lambda_function.this.handler == null
    error_message = "コンテナイメージでは filename / runtime / handler を持たない"
  }
  assert {
    condition     = aws_lambda_function.this.tracing_config[0].mode == "PassThrough"
    error_message = "tracing_mode を変えられる"
  }
  assert {
    condition     = length(aws_lambda_function.this.environment) == 0
    error_message = "環境変数が無ければ environment ブロックを作らない"
  }
  assert {
    condition     = aws_lambda_function.this.reserved_concurrent_executions == -1
    error_message = "既定では同時実行数を予約しない"
  }
}

run "rejects_both_filename_and_image_uri" {
  command = plan
  variables {
    filename  = "build/order-events.zip"
    image_uri = "123456789012.dkr.ecr.us-east-1.amazonaws.com/order-events:1.2.3"
  }
  expect_failures = [var.filename]
}

run "rejects_no_package" {
  command = plan
  variables {
    runtime = "python3.12"
    handler = "app.handler"
  }
  expect_failures = [var.filename]
}

run "rejects_zip_without_runtime" {
  command = plan
  variables {
    filename = "build/order-events.zip"
    handler  = "app.handler"
  }
  expect_failures = [var.runtime]
}

run "rejects_image_with_runtime" {
  command = plan
  variables {
    image_uri = "123456789012.dkr.ecr.us-east-1.amazonaws.com/order-events:1.2.3"
    runtime   = "python3.12"
    handler   = "app.handler"
  }
  expect_failures = [var.runtime]
}

run "rejects_invalid_reserved_concurrency" {
  command = plan
  variables {
    filename                       = "build/order-events.zip"
    runtime                        = "python3.12"
    handler                        = "app.handler"
    reserved_concurrent_executions = -2
  }
  expect_failures = [var.reserved_concurrent_executions]
}

run "rejects_timeout_over_limit" {
  command = plan
  variables {
    filename = "build/order-events.zip"
    runtime  = "python3.12"
    handler  = "app.handler"
    timeout  = 901
  }
  expect_failures = [var.timeout]
}

run "rejects_unknown_tracing_mode" {
  command = plan
  variables {
    filename     = "build/order-events.zip"
    runtime      = "python3.12"
    handler      = "app.handler"
    tracing_mode = "Disabled"
  }
  expect_failures = [var.tracing_mode]
}
