variable "alarm_name" {
  description = "アラーム名（アカウント内で一意）"
  type        = string
  validation {
    condition     = length(var.alarm_name) > 0 && length(var.alarm_name) <= 255
    error_message = "alarm_name は 1〜255 文字"
  }
}

variable "namespace" {
  description = "エラー数・リクエスト数メトリクスの名前空間（例: AWS/ApplicationELB、Example/App）"
  type        = string
}

variable "error_metric_name" {
  description = "分子: エラー数のメトリクス名（例: HTTPCode_Target_5XX_Count、ErrorCount）"
  type        = string
}

variable "request_metric_name" {
  description = "分母: リクエスト数のメトリクス名（例: RequestCount）"
  type        = string
}

variable "dimensions" {
  description = "両メトリクスに共通のディメンション（例: { LoadBalancer = \"app/example/0123456789abcdef\" }）"
  type        = map(string)
  default     = {}
}

variable "period" {
  description = "集計期間（秒）。60 の倍数"
  type        = number
  default     = 60
  validation {
    condition     = var.period >= 60 && var.period % 60 == 0
    error_message = "period は 60 の倍数（秒）"
  }
}

variable "threshold_percent" {
  description = "この値（%）を超えたらアラーム。0 より大きく 100 以下"
  type        = number
  default     = 5
  validation {
    condition     = var.threshold_percent > 0 && var.threshold_percent <= 100
    error_message = "threshold_percent は 0 より大きく 100 以下"
  }
}

variable "evaluation_periods" {
  description = "判定に使う直近の期間数"
  type        = number
  default     = 5
  validation {
    condition     = var.evaluation_periods >= 1 && floor(var.evaluation_periods) == var.evaluation_periods
    error_message = "evaluation_periods は 1 以上の整数"
  }
}

variable "datapoints_to_alarm" {
  description = "evaluation_periods のうち何期間がしきい値超えなら発報するか（M of N）。null なら evaluation_periods と同じ（全期間）"
  type        = number
  default     = null
  validation {
    condition     = var.datapoints_to_alarm == null || (var.datapoints_to_alarm >= 1 && var.datapoints_to_alarm <= var.evaluation_periods)
    error_message = "datapoints_to_alarm は 1 以上 evaluation_periods 以下"
  }
}

variable "alarm_actions" {
  description = "ALARM 状態になったときに通知する SNS トピック ARN の一覧"
  type        = list(string)
  validation {
    condition     = length(var.alarm_actions) > 0 && alltrue([for a in var.alarm_actions : can(regex("^arn:aws:sns:[a-z0-9-]+:[0-9]{12}:", a))])
    error_message = "alarm_actions は SNS トピック ARN を 1 つ以上"
  }
}

variable "ok_actions" {
  description = "OK に戻ったときに通知する SNS トピック ARN の一覧。空なら復旧通知なし"
  type        = list(string)
  default     = []
}

variable "tags" {
  description = "全リソースに付けるタグ"
  type        = map(string)
  default     = {}
}
