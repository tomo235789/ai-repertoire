variable "name" {
  description = "ロール名（アカウント内で一意。変更すると再作成）"
  type        = string
  validation {
    condition     = can(regex("^[A-Za-z0-9+=,.@_-]{1,64}$", var.name))
    error_message = "name は 1〜64 文字の英数字と + = , . @ _ - にすること。"
  }
}

variable "principal_type" {
  description = "ロールを引き受ける主体の種別。service = AWS サービス（ECS タスク・Lambda など）、oidc = 外部 ID プロバイダ（GitHub Actions・EKS Pod Identity Webhook など）"
  type        = string
  validation {
    condition     = contains(["service", "oidc"], var.principal_type)
    error_message = "principal_type は service か oidc にすること。"
  }
}

variable "service_principal" {
  description = "principal_type = service のときのサービス principal（例: ecs-tasks.amazonaws.com）"
  type        = string
  default     = null
  validation {
    condition     = var.service_principal == null || can(regex("^[a-z0-9.-]+\\.amazonaws\\.com$", var.service_principal))
    error_message = "service_principal は <service>.amazonaws.com 形式にすること。"
  }
}

variable "oidc_provider_arn" {
  description = "principal_type = oidc のときの IAM OIDC プロバイダの ARN（例: arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com）"
  type        = string
  default     = null
  validation {
    condition     = var.oidc_provider_arn == null || can(regex("^arn:aws[a-z-]*:iam::[0-9]{12}:oidc-provider/.+$", var.oidc_provider_arn))
    error_message = "oidc_provider_arn は arn:aws:iam::<account>:oidc-provider/<host> 形式にすること。"
  }
}

variable "oidc_subjects" {
  description = "principal_type = oidc のときに許可するトークンの sub クレーム（例: repo:example-org/example-repo:ref:refs/heads/main）。`*` を含めると StringLike で比較する"
  type        = list(string)
  default     = []
}

variable "oidc_audiences" {
  description = "principal_type = oidc のときに許可する aud クレーム"
  type        = list(string)
  default     = ["sts.amazonaws.com"]
}

variable "policy_arns" {
  description = "ロールに付ける管理ポリシーの ARN（例: iam-read-only-policy の policy_arn）"
  type        = list(string)
  default     = []
  validation {
    condition     = alltrue([for p in var.policy_arns : startswith(p, "arn:")])
    error_message = "policy_arns は arn: で始まる管理ポリシーの ARN にすること。"
  }
}

variable "permissions_boundary_arn" {
  description = "ロールに付ける permissions boundary の ARN。null なら付けない"
  type        = string
  default     = null
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
