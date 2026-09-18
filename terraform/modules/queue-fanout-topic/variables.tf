variable "topic_name" {
  description = "イベントを発行する SNS トピック名（標準トピック。.fifo は不可）"
  type        = string
  validation {
    condition     = can(regex("^[A-Za-z0-9_-]{1,256}$", var.topic_name)) && !endswith(var.topic_name, ".fifo")
    error_message = "topic_name は英数字と _ - の 256 文字以内で、.fifo で終わらないようにする。"
  }
}

variable "queue_names" {
  description = "トピックを購読する SQS キュー名のリスト（1 つ以上、重複なし、標準キュー）。購読者ごとに 1 キュー作る"
  type        = list(string)
  validation {
    condition     = length(var.queue_names) > 0 && length(distinct(var.queue_names)) == length(var.queue_names)
    error_message = "queue_names は 1 つ以上で重複しないようにする。"
  }
  validation {
    condition     = alltrue([for n in var.queue_names : can(regex("^[A-Za-z0-9_-]{1,80}$", n)) && !endswith(n, ".fifo")])
    error_message = "queue_names の各要素は英数字と _ - の 80 文字以内で、.fifo で終わらないようにする。"
  }
}

variable "raw_message_delivery" {
  description = "SNS の JSON エンベロープを外して発行メッセージ本文をそのままキューへ入れるか。false なら本文は SNS の通知 JSON（Message フィールドに元の本文）になる"
  type        = bool
  default     = false
}

variable "visibility_timeout_seconds" {
  description = "各キューの可視性タイムアウト秒数（0〜43200）"
  type        = number
  default     = 30
  validation {
    condition     = var.visibility_timeout_seconds >= 0 && var.visibility_timeout_seconds <= 43200
    error_message = "visibility_timeout_seconds は 0〜43200 にする。"
  }
}

variable "message_retention_seconds" {
  description = "各キューのメッセージ保持秒数（60〜1209600）。既定 4 日"
  type        = number
  default     = 345600
  validation {
    condition     = var.message_retention_seconds >= 60 && var.message_retention_seconds <= 1209600
    error_message = "message_retention_seconds は 60〜1209600 にする。"
  }
}

variable "kms_key_id" {
  description = "トピックとキューの保存時暗号化に使う顧客管理 KMS キー（ID / ARN / alias）。null ならキューは SSE-SQS、トピックは暗号化なし（SNS に AWS 管理の既定暗号化は無い）。指定する場合はキーポリシーで sns.amazonaws.com に kms:GenerateDataKey* と kms:Decrypt を許可する"
  type        = string
  default     = null
}

variable "tags" {
  description = "すべてのリソースに付けるタグ（aws_sns_topic_subscription と aws_sqs_queue_policy はタグを持たない）"
  type        = map(string)
  default     = {}
}
