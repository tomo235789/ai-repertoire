variable "name" {
  description = "シークレット名。アプリケーションはこの名前（または出力の ARN）を実行時に GetSecretValue で参照する"
  type        = string
  validation {
    condition     = can(regex("^[A-Za-z0-9/_+=.@-]{1,512}$", var.name))
    error_message = "name は英数字と / _ + = . @ - のみ、1〜512 文字にする。"
  }
}

variable "description" {
  description = "シークレットの説明（何の資格情報か。値そのものは書かない）"
  type        = string
  default     = ""
}

variable "kms_key_arn" {
  description = "保存時暗号化に使う顧客管理 KMS キーの ARN。null なら AWS 管理キー aws/secretsmanager を使う。指定すると読み取りポリシーに kms:Decrypt（Secrets Manager 経由のみ）を加える"
  type        = string
  default     = null
  validation {
    condition     = var.kms_key_arn == null || can(regex("^arn:aws[a-z-]*:kms:[a-z0-9-]+:[0-9]{12}:key/", var.kms_key_arn))
    error_message = "kms_key_arn は arn:aws:kms:<region>:<account>:key/<id> 形式の ARN にする（alias や key id は不可）。"
  }
}

variable "recovery_window_in_days" {
  description = "destroy 後に復旧できる猶予日数（7〜30）。0（即時削除）は許可しない"
  type        = number
  default     = 30
  validation {
    condition     = var.recovery_window_in_days >= 7 && var.recovery_window_in_days <= 30
    error_message = "recovery_window_in_days は 7〜30 にする（0 の即時削除は不可）。"
  }
}

variable "read_policy_name" {
  description = "読み取り用 IAM ポリシー名。null なら <name の / を - に置換>-read"
  type        = string
  default     = null
}

variable "tags" {
  description = "すべてのリソースに付けるタグ"
  type        = map(string)
  default     = {}
}
