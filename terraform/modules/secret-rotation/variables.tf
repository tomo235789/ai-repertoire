variable "secret_arn" {
  description = "ローテーション対象の Secrets Manager シークレットの ARN（secret-fetch-at-runtime の secret_arn 出力など）"
  type        = string
  validation {
    condition     = can(regex("^arn:aws[a-z-]*:secretsmanager:[a-z0-9-]+:[0-9]{12}:secret:", var.secret_arn))
    error_message = "secret_arn は arn:aws:secretsmanager:<region>:<account>:secret:<name> 形式の ARN にする。"
  }
}

variable "rotation_lambda_arn" {
  description = "ローテーションを実行する Lambda 関数の ARN。関数本体と、Secrets Manager がこの関数を呼ぶ lambda:InvokeFunction 許可（aws_lambda_permission）は module の外で用意する"
  type        = string
  validation {
    condition     = can(regex("^arn:aws[a-z-]*:lambda:[a-z0-9-]+:[0-9]{12}:function:", var.rotation_lambda_arn))
    error_message = "rotation_lambda_arn は arn:aws:lambda:<region>:<account>:function:<name> 形式の ARN にする。"
  }
}

variable "rotation_days" {
  description = "自動ローテーションの間隔（日）。1〜1000"
  type        = number
  default     = 30
  validation {
    condition     = var.rotation_days >= 1 && var.rotation_days <= 1000 && floor(var.rotation_days) == var.rotation_days
    error_message = "rotation_days は 1〜1000 の整数にする。"
  }
}

variable "rotate_immediately" {
  description = "適用直後に 1 回ローテーションするか。false にすると次回予定日まで待つ（利用側がまだ新しい値を読めない場合は false にする）"
  type        = bool
  default     = true
}
