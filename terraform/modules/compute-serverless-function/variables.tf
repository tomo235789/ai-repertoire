variable "function_name" {
  description = "Lambda 関数名（変更すると再作成）。ロググループ名 /aws/lambda/<function_name> にも使う"
  type        = string

  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]{1,64}$", var.function_name))
    error_message = "function_name は英数字・ハイフン・アンダースコアで 1〜64 文字"
  }
}

variable "role_arn" {
  description = "関数の実行ロールの ARN（iam-least-privilege-role で作ったもの）"
  type        = string

  validation {
    condition     = can(regex("^arn:aws[a-z-]*:iam::[0-9]{12}:role/", var.role_arn))
    error_message = "role_arn は IAM ロールの ARN"
  }
}

variable "filename" {
  description = "Zip パッケージのローカルパス。image_uri とどちらか一方だけ指定する"
  type        = string
  default     = null

  validation {
    condition     = (var.filename != null) != (var.image_uri != null)
    error_message = "filename と image_uri のどちらか一方だけを指定する"
  }
}

variable "image_uri" {
  description = "コンテナイメージの URI（ECR）。filename とどちらか一方だけ指定する"
  type        = string
  default     = null
}

variable "source_code_hash" {
  description = "Zip パッケージの base64 SHA256（filebase64sha256(filename)）。変更検知に使う。image_uri のときは null"
  type        = string
  default     = null
}

variable "runtime" {
  description = "ランタイム（例 python3.12、nodejs20.x）。Zip パッケージでは必須、image_uri では null"
  type        = string
  default     = null

  validation {
    condition     = var.image_uri != null || (var.runtime != null && var.handler != null)
    error_message = "Zip パッケージ（filename）では runtime と handler が必須"
  }

  validation {
    condition     = var.image_uri == null || (var.runtime == null && var.handler == null)
    error_message = "コンテナイメージ（image_uri）では runtime と handler を指定できない"
  }
}

variable "handler" {
  description = "ハンドラ（例 app.handler）。Zip パッケージでは必須、image_uri では null"
  type        = string
  default     = null
}

variable "environment" {
  description = "関数の環境変数（秘密情報は入れない。secret-fetch-at-runtime を使う）"
  type        = map(string)
  default     = {}
}

variable "timeout" {
  description = "タイムアウト（秒、1〜900）"
  type        = number
  default     = 30

  validation {
    condition     = var.timeout >= 1 && var.timeout <= 900
    error_message = "timeout は 1〜900 秒"
  }
}

variable "memory_size" {
  description = "メモリ（MB、128〜10240）"
  type        = number
  default     = 256

  validation {
    condition     = var.memory_size >= 128 && var.memory_size <= 10240
    error_message = "memory_size は 128〜10240 MB"
  }
}

variable "reserved_concurrent_executions" {
  description = "予約済み同時実行数。-1 で予約なし（アカウントの共有プールを使う）、0 で呼び出し停止"
  type        = number
  default     = -1

  validation {
    condition     = var.reserved_concurrent_executions >= -1 && floor(var.reserved_concurrent_executions) == var.reserved_concurrent_executions
    error_message = "reserved_concurrent_executions は -1 以上の整数"
  }
}

variable "tracing_mode" {
  description = "X-Ray トレース。Active で全呼び出しをトレース、PassThrough で上流のヘッダに従う"
  type        = string
  default     = "Active"

  validation {
    condition     = contains(["Active", "PassThrough"], var.tracing_mode)
    error_message = "tracing_mode は Active か PassThrough"
  }
}

variable "log_retention_days" {
  description = "CloudWatch Logs の保持日数"
  type        = number
  default     = 30

  validation {
    condition     = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653], var.log_retention_days)
    error_message = "log_retention_days は CloudWatch Logs が受け付ける値（1, 3, 5, 7, 14, 30, 60, 90, ... 3653）"
  }
}

variable "tags" {
  description = "全リソースに付けるタグ"
  type        = map(string)
  default     = {}
}
