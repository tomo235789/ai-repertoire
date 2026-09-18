variable "identifier" {
  description = "DB インスタンス識別子。英小文字・数字・ハイフン、先頭は英字、63 文字以内"
  type        = string
  validation {
    condition     = can(regex("^[a-z][a-z0-9-]{0,62}$", var.identifier)) && !endswith(var.identifier, "-") && !strcontains(var.identifier, "--")
    error_message = "identifier は英小文字で始まり、英小文字・数字・ハイフンのみ、末尾ハイフンと連続ハイフンは不可、63 文字以内"
  }
}

variable "engine" {
  description = "DB エンジン（postgres / mysql / mariadb）"
  type        = string
  default     = "postgres"
  validation {
    condition     = contains(["postgres", "mysql", "mariadb"], var.engine)
    error_message = "engine は postgres / mysql / mariadb のいずれか"
  }
}

variable "engine_version" {
  description = "エンジンのメジャーバージョン（例: \"16\"）"
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

variable "db_subnet_group_name" {
  description = "プライベートサブネットで構成した DB サブネットグループ名"
  type        = string
}

variable "vpc_security_group_ids" {
  description = "アプリケーションからの接続だけを許可したセキュリティグループ ID の一覧"
  type        = list(string)
  validation {
    condition     = length(var.vpc_security_group_ids) > 0
    error_message = "vpc_security_group_ids は 1 つ以上"
  }
}

variable "backup_retention_period" {
  description = "自動バックアップの保持日数（1〜35）。0 は自動バックアップの無効化を意味するので受け付けない"
  type        = number
  default     = 7
  validation {
    condition     = var.backup_retention_period >= 1 && var.backup_retention_period <= 35 && floor(var.backup_retention_period) == var.backup_retention_period
    error_message = "backup_retention_period は 1〜35 の整数。0 は自動バックアップとポイントインタイムリカバリを無効にするので不可"
  }
}

variable "backup_window" {
  description = "自動バックアップを取る UTC の時間帯 hh24:mi-hh24:mi（30 分以上、メンテナンスウィンドウと重ねない）。例: 18:00-19:00（JST 03:00-04:00）"
  type        = string
  validation {
    condition     = can(regex("^([01][0-9]|2[0-3]):[0-5][0-9]-([01][0-9]|2[0-3]):[0-5][0-9]$", var.backup_window))
    error_message = "backup_window は UTC の hh24:mi-hh24:mi 形式（例: 18:00-19:00）"
  }
}

variable "copy_tags_to_snapshot" {
  description = "インスタンスのタグをスナップショットにも付ける（コスト配賦・保持ポリシーの根拠になる）"
  type        = bool
  default     = true
}

variable "delete_automated_backups" {
  description = "インスタンス削除時に自動バックアップも消すか。false なら保持期間が切れるまで残る"
  type        = bool
  default     = false
}

variable "final_snapshot_identifier" {
  description = "インスタンス削除時に取る最終スナップショットの名前。必ず取る（skip_final_snapshot は常に false）"
  type        = string
  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9-]{0,254}$", var.final_snapshot_identifier)) && !endswith(var.final_snapshot_identifier, "-") && !strcontains(var.final_snapshot_identifier, "--")
    error_message = "final_snapshot_identifier は英字で始まり、英数字とハイフンのみ、末尾ハイフンと連続ハイフンは不可、255 文字以内"
  }
}

variable "tags" {
  description = "全リソースに付けるタグ"
  type        = map(string)
  default     = {}
}
