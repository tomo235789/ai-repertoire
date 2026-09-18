variable "name" {
  description = "ロググループ名（例: /app/example/api）"
  type        = string
  validation {
    condition     = can(regex("^[A-Za-z0-9_/.#-]{1,512}$", var.name))
    error_message = "ロググループ名は英数字と _ / . # - のみ、512 文字以内"
  }
}

variable "retention_in_days" {
  description = "ログの保持日数。CloudWatch Logs が許す値だけ受け付ける（0 は無期限）"
  type        = number
  default     = 30
  validation {
    condition     = contains([0, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653], var.retention_in_days)
    error_message = "retention_in_days は 0, 1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653 のいずれか"
  }
}

variable "kms_key_id" {
  description = "ログを暗号化する KMS キーの ARN。null なら CloudWatch Logs の既定暗号化（AWS 管理）。キーポリシーで logs.<region>.amazonaws.com を許可しておく"
  type        = string
  default     = null
  validation {
    condition     = var.kms_key_id == null || can(regex("^arn:aws:kms:[a-z0-9-]+:[0-9]{12}:key/", var.kms_key_id))
    error_message = "kms_key_id は KMS キーの ARN（arn:aws:kms:<region>:<account>:key/<id>）"
  }
}

variable "metric_namespace" {
  description = "メトリクスフィルタが出力する CloudWatch メトリクスの名前空間（例: Example/App）"
  type        = string
  default     = null
}

variable "metric_filters" {
  description = "JSON ログから切り出すメトリクス。キーはフィルタ名、pattern は CloudWatch Logs のフィルタパターン（例: { $.level = \"error\" }）、metric_value は 1 件ごとに加算する値、default_value は一致が無い期間に出す値"
  type = map(object({
    pattern       = string
    metric_name   = string
    metric_value  = optional(string, "1")
    default_value = optional(number, 0)
  }))
  default = {}
  validation {
    condition     = alltrue([for f in values(var.metric_filters) : can(regex("^[A-Za-z0-9_./-]{1,255}$", f.metric_name))])
    error_message = "metric_name は英数字と _ . / - のみ、255 文字以内"
  }
}

variable "tags" {
  description = "全リソースに付けるタグ（メトリクスフィルタはタグ非対応）"
  type        = map(string)
  default     = {}
}
