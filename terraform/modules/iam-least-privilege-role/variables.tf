variable "name" {
  description = "ロール名（アカウント内で一意。変更すると再作成）"
  type        = string
  validation {
    condition     = can(regex("^[A-Za-z0-9+=,.@_-]{1,64}$", var.name))
    error_message = "name は 1〜64 文字の英数字と + = , . @ _ - にすること。"
  }
}

variable "trusted_service" {
  description = "このロールを引き受けられる AWS サービスの principal（例: lambda.amazonaws.com、ecs-tasks.amazonaws.com）"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9.-]+\\.amazonaws\\.com$", var.trusted_service))
    error_message = "trusted_service は <service>.amazonaws.com 形式のサービス principal にすること。"
  }
}

variable "allowed_actions" {
  description = "許可する IAM アクション。s3:GetObject のような完全指定か s3:Get* のような接頭辞。`*` や s3:* のようなサービス全体の許可は弾く"
  type        = list(string)
  validation {
    condition     = length(var.allowed_actions) > 0
    error_message = "allowed_actions は 1 つ以上指定すること。"
  }
  validation {
    condition     = alltrue([for a in var.allowed_actions : can(regex("^[a-z0-9-]+:[A-Za-z0-9]+\\*?$", a))])
    error_message = "allowed_actions は <service>:<Action> か <service>:<Prefix>* の形にすること。`*` や <service>:* は最小権限にならないので許可しない。"
  }
}

variable "resource_arns" {
  description = "許可対象のリソース ARN。arn:aws:s3:::bucket/* のような ARN 内のワイルドカードは可、`*` 単独は不可"
  type        = list(string)
  validation {
    condition     = length(var.resource_arns) > 0
    error_message = "resource_arns は 1 つ以上指定すること。"
  }
  validation {
    condition     = alltrue([for r in var.resource_arns : r != "*" && startswith(r, "arn:")])
    error_message = "resource_arns は arn: で始まる ARN にすること。`*`（全リソース）は最小権限にならないので許可しない。"
  }
}

variable "permissions_boundary_arn" {
  description = "ロールに付ける permissions boundary（管理ポリシー）の ARN。null なら付けない"
  type        = string
  default     = null
  validation {
    condition     = var.permissions_boundary_arn == null || can(regex("^arn:aws[a-z-]*:iam::[0-9]{12}:policy/", var.permissions_boundary_arn))
    error_message = "permissions_boundary_arn は IAM 管理ポリシーの ARN（arn:aws:iam::<account>:policy/...）か null にすること。"
  }
}

variable "max_session_duration" {
  description = "引き受けたセッションの最長秒数（3600〜43200）"
  type        = number
  default     = 3600
  validation {
    condition     = var.max_session_duration >= 3600 && var.max_session_duration <= 43200
    error_message = "max_session_duration は 3600〜43200 秒にすること。"
  }
}

variable "tags" {
  description = "全リソースに付けるタグ"
  type        = map(string)
  default     = {}
}
