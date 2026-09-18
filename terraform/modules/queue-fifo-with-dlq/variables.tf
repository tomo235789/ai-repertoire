variable "name" {
  description = "キュー名。FIFO なので .fifo で終える（例: example-orders.fifo）"
  type        = string
  validation {
    condition     = can(regex("^[A-Za-z0-9_-]{1,75}\\.fifo$", var.name))
    error_message = "name は英数字と _ - で、.fifo で終わる 80 文字以内にする。"
  }
}

variable "dlq_name" {
  description = "デッドレターキュー名（.fifo で終える）。null なら <name の .fifo の前>-dlq.fifo"
  type        = string
  default     = null
  validation {
    condition     = var.dlq_name == null || can(regex("^[A-Za-z0-9_-]{1,75}\\.fifo$", var.dlq_name))
    error_message = "dlq_name は英数字と _ - で、.fifo で終わる 80 文字以内にする。"
  }
}

variable "max_receive_count" {
  description = "この回数受信しても削除されなかったメッセージを DLQ へ移す（1〜1000）"
  type        = number
  default     = 5
  validation {
    condition     = var.max_receive_count >= 1 && var.max_receive_count <= 1000
    error_message = "max_receive_count は 1〜1000 にする。"
  }
}

variable "visibility_timeout_seconds" {
  description = "受信後に他のコンシューマから見えなくなる秒数（0〜43200）。処理時間の上限より長くする"
  type        = number
  default     = 30
  validation {
    condition     = var.visibility_timeout_seconds >= 0 && var.visibility_timeout_seconds <= 43200
    error_message = "visibility_timeout_seconds は 0〜43200 にする。"
  }
}

variable "message_retention_seconds" {
  description = "メインキューのメッセージ保持秒数（60〜1209600）。既定 4 日"
  type        = number
  default     = 345600
  validation {
    condition     = var.message_retention_seconds >= 60 && var.message_retention_seconds <= 1209600
    error_message = "message_retention_seconds は 60〜1209600 にする。"
  }
}

variable "dlq_message_retention_seconds" {
  description = "DLQ のメッセージ保持秒数（60〜1209600）。既定 14 日。メインキューの保持秒数以上にする（DLQ 内の残り時間は元の送信時刻から数える）"
  type        = number
  default     = 1209600
  validation {
    condition     = var.dlq_message_retention_seconds >= 60 && var.dlq_message_retention_seconds <= 1209600
    error_message = "dlq_message_retention_seconds は 60〜1209600 にする。"
  }
}

variable "content_based_deduplication" {
  description = "メッセージ本文の SHA-256 で重複排除するか。false なら送信側が MessageDeduplicationId を必ず付ける"
  type        = bool
  default     = false
}

variable "high_throughput" {
  description = "高スループット FIFO（重複排除とスループット制限をメッセージグループ単位にする）を有効にするか"
  type        = bool
  default     = false
}

variable "kms_key_id" {
  description = "保存時暗号化に使う顧客管理 KMS キー（ID / ARN / alias）。null なら SQS 管理キー（SSE-SQS）で暗号化する"
  type        = string
  default     = null
}

variable "kms_data_key_reuse_period_seconds" {
  description = "kms_key_id 指定時にデータキーを再利用する秒数（60〜86400）。長いほど KMS 呼び出しが減る"
  type        = number
  default     = 300
  validation {
    condition     = var.kms_data_key_reuse_period_seconds >= 60 && var.kms_data_key_reuse_period_seconds <= 86400
    error_message = "kms_data_key_reuse_period_seconds は 60〜86400 にする。"
  }
}

variable "tags" {
  description = "すべてのリソースに付けるタグ"
  type        = map(string)
  default     = {}
}
