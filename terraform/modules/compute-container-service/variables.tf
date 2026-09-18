variable "name" {
  description = "サービス名。タスク定義のファミリ名・コンテナ名・ロググループ名（/ecs/<name>）にも使う"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]{1,255}$", var.name))
    error_message = "name は英数字・ハイフン・アンダースコアで 1〜255 文字"
  }
}

variable "cluster" {
  description = "サービスを置く ECS クラスタの ARN か名前"
  type        = string

  validation {
    condition     = length(var.cluster) > 0
    error_message = "cluster は空にできない"
  }
}

variable "image" {
  description = "コンテナイメージ（例 123456789012.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3）。タグは latest ではなく固定する"
  type        = string

  validation {
    condition     = length(var.image) > 0
    error_message = "image は空にできない"
  }
}

variable "cpu" {
  description = "タスクの CPU ユニット（Fargate が受け付ける値のみ）"
  type        = number
  default     = 256

  validation {
    condition     = contains([256, 512, 1024, 2048, 4096, 8192, 16384], var.cpu)
    error_message = "cpu は 256 / 512 / 1024 / 2048 / 4096 / 8192 / 16384"
  }
}

variable "memory" {
  description = "タスクのメモリ（MiB）。cpu との組み合わせは Fargate の対応表に従う"
  type        = number
  default     = 512

  validation {
    condition     = var.memory == 512 || (var.memory >= 1024 && var.memory <= 122880 && var.memory % 1024 == 0)
    error_message = "memory は 512 か 1024 の倍数（最大 122880）"
  }
}

variable "desired_count" {
  description = "常駐させるタスク数"
  type        = number
  default     = 2

  validation {
    condition     = var.desired_count >= 0 && floor(var.desired_count) == var.desired_count
    error_message = "desired_count は 0 以上の整数"
  }
}

variable "container_port" {
  description = "コンテナが待ち受けるポート"
  type        = number
  default     = 8080

  validation {
    condition     = var.container_port >= 1 && var.container_port <= 65535
    error_message = "container_port は 1〜65535"
  }
}

variable "subnet_ids" {
  description = "タスクを置くプライベートサブネットの ID（network-private-subnet の subnet_id）"
  type        = list(string)

  validation {
    condition     = length(var.subnet_ids) > 0
    error_message = "subnet_ids は 1 つ以上"
  }
}

variable "security_group_ids" {
  description = "タスクの ENI に付けるセキュリティグループの ID（network-security-group-minimal の security_group_id）"
  type        = list(string)

  validation {
    condition     = length(var.security_group_ids) > 0
    error_message = "security_group_ids は 1 つ以上"
  }
}

variable "execution_role_arn" {
  description = "ECS エージェントがイメージ取得とログ出力に使う実行ロールの ARN"
  type        = string

  validation {
    condition     = can(regex("^arn:aws[a-z-]*:iam::[0-9]{12}:role/", var.execution_role_arn))
    error_message = "execution_role_arn は IAM ロールの ARN"
  }
}

variable "task_role_arn" {
  description = "コンテナ内のアプリが AWS API を呼ぶときに使うタスクロールの ARN。AWS API を呼ばないなら null"
  type        = string
  default     = null

  validation {
    condition     = var.task_role_arn == null || can(regex("^arn:aws[a-z-]*:iam::[0-9]{12}:role/", var.task_role_arn))
    error_message = "task_role_arn は IAM ロールの ARN"
  }
}

variable "environment" {
  description = "コンテナの環境変数（秘密情報は入れない。secret-fetch-at-runtime を使う）"
  type        = map(string)
  default     = {}
}

variable "region" {
  description = "ロググループのあるリージョン（awslogs-region）"
  type        = string

  validation {
    condition     = can(regex("^[a-z]{2}(-[a-z]+)+-[0-9]$", var.region))
    error_message = "region は us-east-1 のような形式"
  }
}

variable "log_retention_days" {
  description = "CloudWatch Logs の保持日数"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653], var.log_retention_days)
    error_message = "log_retention_days は CloudWatch Logs が受け付ける値（1, 3, 5, 7, 14, 30, 60, 90, ... 3653）"
  }
}

variable "tags" {
  description = "全リソースに付けるタグ"
  type        = map(string)
  default     = {}
}
