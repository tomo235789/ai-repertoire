mock_provider "aws" {}

variables {
  name               = "app"
  cluster            = "arn:aws:ecs:us-east-1:123456789012:cluster/example"
  image              = "123456789012.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3"
  subnet_ids         = ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"]
  security_group_ids = ["sg-0123456789abcdef0"]
  execution_role_arn = "arn:aws:iam::123456789012:role/app-execution"
  task_role_arn      = "arn:aws:iam::123456789012:role/app-task"
  region             = "us-east-1"
  environment        = { LOG_LEVEL = "info" }
  tags               = { env = "example" }
}

run "fargate_service_in_private_subnets" {
  command = plan

  assert {
    condition     = aws_ecs_service.this.launch_type == "FARGATE"
    error_message = "起動タイプは Fargate"
  }
  assert {
    condition     = aws_ecs_service.this.network_configuration[0].assign_public_ip == false
    error_message = "タスクにパブリック IP を付けてはならない"
  }
  assert {
    condition     = length(aws_ecs_service.this.network_configuration[0].subnets) == 2 && contains(aws_ecs_service.this.network_configuration[0].security_groups, "sg-0123456789abcdef0")
    error_message = "指定したサブネットと SG にタスクを置く"
  }
  assert {
    condition     = aws_ecs_service.this.desired_count == 2
    error_message = "desired_count の既定値は 2"
  }
  assert {
    condition     = aws_ecs_service.this.deployment_circuit_breaker[0].enable == true && aws_ecs_service.this.deployment_circuit_breaker[0].rollback == true
    error_message = "デプロイ失敗時は自動ロールバックする"
  }
  assert {
    condition     = contains(aws_ecs_task_definition.this.requires_compatibilities, "FARGATE") && aws_ecs_task_definition.this.network_mode == "awsvpc"
    error_message = "タスク定義は Fargate 互換・awsvpc"
  }
  assert {
    condition     = aws_ecs_task_definition.this.cpu == "256" && aws_ecs_task_definition.this.memory == "512"
    error_message = "cpu / memory の既定値は 256 / 512"
  }
  assert {
    condition     = aws_ecs_task_definition.this.execution_role_arn == "arn:aws:iam::123456789012:role/app-execution" && aws_ecs_task_definition.this.task_role_arn == "arn:aws:iam::123456789012:role/app-task"
    error_message = "実行ロールとタスクロールは入力どおり"
  }
  assert {
    condition     = jsondecode(aws_ecs_task_definition.this.container_definitions)[0].image == "123456789012.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3"
    error_message = "コンテナイメージは入力どおり"
  }
  assert {
    condition     = jsondecode(aws_ecs_task_definition.this.container_definitions)[0].logConfiguration.logDriver == "awslogs"
    error_message = "ログドライバは awslogs"
  }
  assert {
    condition     = jsondecode(aws_ecs_task_definition.this.container_definitions)[0].logConfiguration.options["awslogs-group"] == "/ecs/app" && jsondecode(aws_ecs_task_definition.this.container_definitions)[0].logConfiguration.options["awslogs-region"] == "us-east-1"
    error_message = "ログは /ecs/<name> のロググループへ"
  }
  assert {
    condition     = jsondecode(aws_ecs_task_definition.this.container_definitions)[0].portMappings[0].containerPort == 8080
    error_message = "container_port の既定値は 8080"
  }
  assert {
    condition     = jsondecode(aws_ecs_task_definition.this.container_definitions)[0].environment[0].name == "LOG_LEVEL" && jsondecode(aws_ecs_task_definition.this.container_definitions)[0].environment[0].value == "info"
    error_message = "環境変数を name / value の配列で渡す"
  }
  assert {
    condition     = aws_cloudwatch_log_group.this.name == "/ecs/app" && aws_cloudwatch_log_group.this.retention_in_days == 30
    error_message = "ロググループは保持期間付き（既定 30 日）"
  }
  assert {
    condition     = aws_ecs_service.this.tags["env"] == "example" && aws_ecs_task_definition.this.tags["env"] == "example" && aws_cloudwatch_log_group.this.tags["env"] == "example"
    error_message = "全リソースに tags を付ける"
  }
  assert {
    condition     = aws_ecs_service.this.propagate_tags == "SERVICE"
    error_message = "サービスのタグをタスクに伝播する"
  }
  assert {
    condition     = output.log_group_name == "/ecs/app"
    error_message = "ロググループ名を出力する"
  }
}

run "task_role_optional" {
  command = plan
  variables {
    task_role_arn = null
    cpu           = 1024
    memory        = 2048
  }

  assert {
    condition     = aws_ecs_task_definition.this.task_role_arn == null
    error_message = "task_role_arn は省略できる"
  }
  assert {
    condition     = aws_ecs_task_definition.this.cpu == "1024" && aws_ecs_task_definition.this.memory == "2048"
    error_message = "cpu / memory は文字列としてタスク定義に渡す"
  }
}

run "rejects_unsupported_cpu" {
  command = plan
  variables {
    cpu = 300
  }
  expect_failures = [var.cpu]
}

run "rejects_unsupported_memory" {
  command = plan
  variables {
    memory = 700
  }
  expect_failures = [var.memory]
}

run "rejects_empty_subnets" {
  command = plan
  variables {
    subnet_ids = []
  }
  expect_failures = [var.subnet_ids]
}

run "rejects_negative_desired_count" {
  command = plan
  variables {
    desired_count = -1
  }
  expect_failures = [var.desired_count]
}

run "rejects_invalid_log_retention" {
  command = plan
  variables {
    log_retention_days = 31
  }
  expect_failures = [var.log_retention_days]
}

run "rejects_non_role_execution_arn" {
  command = plan
  variables {
    execution_role_arn = "arn:aws:iam::123456789012:user/alice"
  }
  expect_failures = [var.execution_role_arn]
}
