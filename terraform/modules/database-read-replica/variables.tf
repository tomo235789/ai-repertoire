variable "identifier" {
  description = "レプリカの DB インスタンス識別子。英小文字・数字・ハイフン、先頭は英字、63 文字以内"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,62}$", var.identifier)) && !endswith(var.identifier, "-") && !strcontains(var.identifier, "--")
    error_message = "identifier は英小文字で始まり、英小文字・数字・ハイフンのみ、末尾ハイフンと連続ハイフンは不可、63 文字以内"
  }
}

variable "replicate_source_db" {
  description = "複製元インスタンス。同一リージョンなら識別子（例: example-db）、クロスリージョンなら ARN（例: arn:aws:rds:us-east-1:123456789012:db:example-db）"
  type        = string
  validation {
    condition     = length(var.replicate_source_db) > 0
    error_message = "replicate_source_db は必須"
  }
}

variable "instance_class" {
  description = "レプリカのインスタンスクラス。読み取り負荷に合わせて元と別のクラスにしてよい"
  type        = string
  default     = "db.t4g.medium"
}

variable "kms_key_id" {
  description = "レプリカ側リージョンの KMS キー ARN。クロスリージョン（replicate_source_db が ARN）では必須。同一リージョンでは null にして元と同じ鍵を使う"
  type        = string
  default     = null
  validation {
    condition     = var.kms_key_id == null || can(regex("^arn:aws:kms:[a-z0-9-]+:[0-9]{12}:key/", var.kms_key_id))
    error_message = "kms_key_id は KMS キーの ARN（arn:aws:kms:<region>:<account>:key/<id>）"
  }
  validation {
    condition     = !startswith(var.replicate_source_db, "arn:") || var.kms_key_id != null
    error_message = "クロスリージョンレプリカ（replicate_source_db が ARN）では複製先リージョンの kms_key_id が必須"
  }
}

variable "vpc_security_group_ids" {
  description = "読み取りクライアントからの接続だけを許可したセキュリティグループ ID の一覧"
  type        = list(string)
  validation {
    condition     = length(var.vpc_security_group_ids) > 0
    error_message = "vpc_security_group_ids は 1 つ以上"
  }
}

variable "db_subnet_group_name" {
  description = "レプリカを置く DB サブネットグループ名。クロスリージョンでは必須。同一リージョンでは null にして元と同じサブネットグループを使う"
  type        = string
  default     = null
  validation {
    condition     = !startswith(var.replicate_source_db, "arn:") || var.db_subnet_group_name != null
    error_message = "クロスリージョンレプリカでは複製先リージョンの db_subnet_group_name が必須"
  }
}

variable "backup_retention_period" {
  description = "レプリカ自身の自動バックアップ保持日数（0〜35）。バックアップは元インスタンスで取るので、レプリカは 0 でよい"
  type        = number
  default     = 0
  validation {
    condition     = var.backup_retention_period >= 0 && var.backup_retention_period <= 35 && floor(var.backup_retention_period) == var.backup_retention_period
    error_message = "backup_retention_period は 0〜35 の整数"
  }
}

variable "multi_az" {
  description = "レプリカ自身をマルチ AZ にする（昇格後にそのまま本番にする場合）"
  type        = bool
  default     = false
}

variable "tags" {
  description = "全リソースに付けるタグ"
  type        = map(string)
  default     = {}
}
