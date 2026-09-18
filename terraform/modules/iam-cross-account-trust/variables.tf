variable "name" {
  description = "ロール名（アカウント内で一意。変更すると再作成）"
  type        = string
  validation {
    condition     = can(regex("^[A-Za-z0-9+=,.@_-]{1,64}$", var.name))
    error_message = "name は 1〜64 文字の英数字と + = , . @ _ - にすること。"
  }
}

variable "trusted_principal_arns" {
  description = "引き受けを許可する別アカウントの principal ARN。アカウント全体なら arn:aws:iam::<account>:root、特定ロールなら arn:aws:iam::<account>:role/<name>"
  type        = list(string)
  validation {
    condition     = length(var.trusted_principal_arns) > 0
    error_message = "trusted_principal_arns は 1 つ以上指定すること。"
  }
  validation {
    condition     = alltrue([for p in var.trusted_principal_arns : can(regex("^arn:aws[a-z-]*:iam::[0-9]{12}:(root|role/.+|user/.+)$", p))])
    error_message = "trusted_principal_arns は arn:aws:iam::<12 桁のアカウント ID>:root / role/... / user/... の形にすること。`*` は許可しない。"
  }
}

variable "external_id" {
  description = "引き受け時に sts:ExternalId として要求する共有秘密。混乱した代理問題を防ぐために必須（2〜1224 文字）"
  type        = string
  sensitive   = true
  validation {
    # RE2 は反復回数の上限が 1000 なので長さは length() で判定する
    condition     = length(var.external_id) >= 2 && length(var.external_id) <= 1224 && can(regex("^[A-Za-z0-9+=,.@:/_-]+$", var.external_id))
    error_message = "external_id は 2〜1224 文字の英数字と + = , . @ : / _ - にすること。空文字や `*` は許可しない。"
  }
}

variable "require_mfa" {
  description = "true なら引き受け元のセッションが MFA 認証済みであることを条件に加える"
  type        = bool
  default     = false
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

variable "max_session_duration" {
  description = "引き受けたセッションの最長秒数（3600〜43200）。ロールチェーンでは 3600 に制限される"
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
