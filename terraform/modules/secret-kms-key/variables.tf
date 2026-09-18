variable "alias_name" {
  description = "キーの別名。alias/ で始める（alias/aws/ は AWS 管理キー用のため不可）。利用側は KMS キー ID ではなくこの別名で参照する"
  type        = string
  validation {
    condition     = can(regex("^alias/[A-Za-z0-9/_-]{1,250}$", var.alias_name)) && !startswith(var.alias_name, "alias/aws/")
    error_message = "alias_name は alias/ で始まる英数字と / _ - にする（alias/aws/ は予約済み）。"
  }
}

variable "description" {
  description = "キーの用途の説明"
  type        = string
  default     = ""
}

variable "account_id" {
  description = "キーを作る AWS アカウント ID（12 桁）。キーポリシーのルート principal に使う"
  type        = string
  validation {
    condition     = can(regex("^[0-9]{12}$", var.account_id))
    error_message = "account_id は 12 桁の数字にする。"
  }
}

variable "partition" {
  description = "AWS パーティション（aws / aws-cn / aws-us-gov）"
  type        = string
  default     = "aws"
  validation {
    condition     = contains(["aws", "aws-cn", "aws-us-gov"], var.partition)
    error_message = "partition は aws / aws-cn / aws-us-gov のいずれかにする。"
  }
}

variable "allow_root_full_access" {
  description = "アカウントのルート principal に kms:* を与えるか。true なら IAM ポリシーでもキーを管理でき、誤ったキーポリシーで自分を締め出す事故を防げる。false にする場合は admin_principal_arns が必須"
  type        = bool
  default     = true
}

variable "admin_principal_arns" {
  description = "キーを管理する（ポリシー変更・無効化・削除予約ができるが暗号化・復号はできない）IAM principal の ARN"
  type        = list(string)
  default     = []
  validation {
    condition     = alltrue([for a in var.admin_principal_arns : can(regex("^arn:aws[a-z-]*:iam::[0-9]{12}:(root|user/|role/)", a))])
    error_message = "admin_principal_arns は IAM の user / role / root の ARN にする。"
  }
}

variable "user_principal_arns" {
  description = "キーで暗号化・復号する（管理はできない）IAM principal の ARN。サービスロールなど"
  type        = list(string)
  default     = []
  validation {
    condition     = alltrue([for a in var.user_principal_arns : can(regex("^arn:aws[a-z-]*:iam::[0-9]{12}:(root|user/|role/)", a))])
    error_message = "user_principal_arns は IAM の user / role / root の ARN にする。"
  }
}

variable "deletion_window_in_days" {
  description = "削除予約から実際に削除されるまでの待機日数（7〜30）。この間は取り消せる"
  type        = number
  default     = 30
  validation {
    condition     = var.deletion_window_in_days >= 7 && var.deletion_window_in_days <= 30
    error_message = "deletion_window_in_days は 7〜30 にする。"
  }
}

variable "tags" {
  description = "キーに付けるタグ（aws_kms_alias はタグを持たない）"
  type        = map(string)
  default     = {}
}
