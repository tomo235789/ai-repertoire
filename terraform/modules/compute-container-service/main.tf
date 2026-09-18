# コンテナを常駐サービスとして Fargate で実行する。
# タスクはプライベートサブネットに置き、パブリック IP を付けない。ログは awslogs で保持期間付きのロググループへ。

locals {
  log_group_name = "/ecs/${var.name}"

  container_definitions = [
    {
      name      = var.name
      image     = var.image
      essential = true
      portMappings = [
        { containerPort = var.container_port, protocol = "tcp" }
      ]
      environment = [for k, v in var.environment : { name = k, value = v }]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = local.log_group_name
          awslogs-region        = var.region
          awslogs-stream-prefix = "ecs"
        }
      }
    }
  ]
}

resource "aws_cloudwatch_log_group" "this" {
  name              = local.log_group_name
  retention_in_days = var.log_retention_days

  tags = var.tags
}

resource "aws_ecs_task_definition" "this" {
  family                   = var.name
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = tostring(var.cpu)
  memory                   = tostring(var.memory)
  execution_role_arn       = var.execution_role_arn
  task_role_arn            = var.task_role_arn
  container_definitions    = jsonencode(local.container_definitions)

  tags = var.tags

  depends_on = [aws_cloudwatch_log_group.this]
}

resource "aws_ecs_service" "this" {
  name            = var.name
  cluster         = var.cluster
  task_definition = aws_ecs_task_definition.this.arn
  desired_count   = var.desired_count
  launch_type     = "FARGATE"
  propagate_tags  = "SERVICE"

  network_configuration {
    subnets          = var.subnet_ids
    security_groups  = var.security_group_ids
    assign_public_ip = false
  }

  # デプロイ失敗時は前のタスク定義へ自動ロールバック
  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  tags = var.tags
}
