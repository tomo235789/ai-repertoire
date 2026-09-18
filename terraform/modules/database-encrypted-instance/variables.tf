variable "identifier" {
  description = "DB インスタンス識別子。英小文字・数字・ハイフン、先頭は英字、63 文字以内"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,62}$", var.identifier)) && !endswith(var.identifier, "-") && !strcontains(var.identifier, "--")
    error_message = "identifier は英小文字で始まり、英小文字・数字・ハイフンのみ、末尾ハイフンと連続ハイフンは不可、63 文字以内"
  }
}

variable "engine_version" {
  description = "PostgreSQL のメジャーバージョン（例: \"16\"）。マイナーは自動更新に任せるのでメジャーだけを書く"
  type        = string
}

variable "instance_class" {
  description = "インスタンスクラス（例: db.t4g.medium）"
  type        = string
  default     = "db.t4g.medium"
}

variable "allocated_storage" {
  description = "初期ストレージ容量（GiB）。gp3 の最小は 20"
  type        = number
  default     = 20
  validation {
    condition     = var.allocated_storage >= 20
    error_message = "allocated_storage は 20 GiB 以上"
  }
}

variable "db_name" {
  description = "作成時に作る初期データベース名"
  type        = string
}

variable "master_username" {
  description = "マスターユーザー名。パスワードは Secrets Manager が生成・保管する（Terraform には書かない）"
  type        = string
  default     = "postgres"
}

variable "kms_key_id" {
  description = "保存時暗号化・マスターパスワード・Performance Insights に使う KMS キーの ARN。null なら AWS 管理キー aws/rds を使う（暗号化自体は常に有効）"
  type        = string
  default     = null
  validation {
    condition     = var.kms_key_id == null || can(regex("^arn:aws:kms:[a-z0-9-]+:[0-9]{12}:key/", var.kms_key_id))
    error_message = "kms_key_id は KMS キーの ARN（arn:aws:kms:<region>:<account>:key/<id>）。エイリアスや ID だけは不可"
  }
}

variable "db_subnet_group_name" {
  description = "プライベートサブネットで構成した DB サブネットグループ名"
  type        = string
}

variable "vpc_security_group_ids" {
  description = "アプリケーションからの 5432 だけを許可したセキュリティグループ ID の一覧"
  type        = list(string)
  validation {
    condition     = length(var.vpc_security_group_ids) > 0
    error_message = "vpc_security_group_ids は 1 つ以上"
  }
}

variable "deletion_protection" {
  description = "削除保護。本番は true のまま。false にするのは破棄する直前だけ"
  type        = bool
  default     = true
}

variable "multi_az" {
  description = "マルチ AZ 配置（スタンバイを別 AZ に置く）"
  type        = bool
  default     = false
}

variable "performance_insights_retention_period" {
  description = "Performance Insights の保持日数。7（無料枠）か 31 の倍数（〜731）"
  type        = number
  default     = 7
  validation {
    condition     = var.performance_insights_retention_period == 7 || (var.performance_insights_retention_period % 31 == 0 && var.performance_insights_retention_period <= 731)
    error_message = "performance_insights_retention_period は 7 か 31 の倍数（最大 731）"
  }
}

variable "tags" {
  description = "全リソースに付けるタグ"
  type        = map(string)
  default     = {}
}
