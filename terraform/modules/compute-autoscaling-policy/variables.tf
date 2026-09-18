variable "cluster_name" {
  description = "対象 ECS サービスが属するクラスタ名（ARN ではなく名前）"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]{1,255}$", var.cluster_name))
    error_message = "cluster_name は英数字・ハイフン・アンダースコアで 1〜255 文字（ARN は不可）"
  }
}

variable "service_name" {
  description = "対象 ECS サービス名（compute-container-service の service_name）"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]{1,255}$", var.service_name))
    error_message = "service_name は英数字・ハイフン・アンダースコアで 1〜255 文字（ARN は不可）"
  }
}

variable "min_capacity" {
  description = "タスク数の下限"
  type        = number

  validation {
    condition     = var.min_capacity >= 0 && floor(var.min_capacity) == var.min_capacity
    error_message = "min_capacity は 0 以上の整数"
  }
}

variable "max_capacity" {
  description = "タスク数の上限（min_capacity 以上）"
  type        = number

  validation {
    condition     = var.max_capacity >= 1 && floor(var.max_capacity) == var.max_capacity
    error_message = "max_capacity は 1 以上の整数"
  }

  validation {
    condition     = var.max_capacity >= var.min_capacity
    error_message = "max_capacity は min_capacity 以上"
  }
}

variable "target_cpu_utilization" {
  description = "維持したい平均 CPU 使用率（%）。これを超えるとスケールアウト、下回るとスケールイン"
  type        = number
  default     = 60

  validation {
    condition     = var.target_cpu_utilization > 0 && var.target_cpu_utilization <= 100
    error_message = "target_cpu_utilization は 0 より大きく 100 以下"
  }
}

variable "scale_out_cooldown" {
  description = "スケールアウト後に次のスケールアウトを待つ秒数"
  type        = number
  default     = 60

  validation {
    condition     = var.scale_out_cooldown >= 0
    error_message = "scale_out_cooldown は 0 以上"
  }
}

variable "scale_in_cooldown" {
  description = "スケールイン後に次のスケールインを待つ秒数（急激な縮退を防ぐため長めにする）"
  type        = number
  default     = 300

  validation {
    condition     = var.scale_in_cooldown >= 0
    error_message = "scale_in_cooldown は 0 以上"
  }
}

variable "tags" {
  description = "スケーラブルターゲットに付けるタグ（aws_appautoscaling_policy はタグを持たない）"
  type        = map(string)
  default     = {}
}
