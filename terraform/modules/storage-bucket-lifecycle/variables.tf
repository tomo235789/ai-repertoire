variable "bucket_name" {
  description = "ライフサイクル規則を付けるバケット名（aws_s3_bucket の id）"
  type        = string
  validation {
    condition     = length(var.bucket_name) >= 3
    error_message = "bucket_name は 3 文字以上のバケット名にすること。"
  }
}

variable "rule_id" {
  description = "規則の ID（1 バケット内で一意）"
  type        = string
  default     = "retention"
}

variable "prefix" {
  description = "規則を適用するキーの prefix。空文字ならバケット全体"
  type        = string
  default     = ""
}

variable "transition_days" {
  description = "作成から何日後に transition_storage_class へ移行するか。null なら移行しない"
  type        = number
  default     = null
  validation {
    condition     = var.transition_days == null || try(var.transition_days >= 1 && floor(var.transition_days) == var.transition_days, false)
    error_message = "transition_days は 1 以上の整数か null にすること。"
  }
}

variable "transition_storage_class" {
  description = "移行先のストレージクラス"
  type        = string
  default     = "STANDARD_IA"
  validation {
    condition     = contains(["STANDARD_IA", "ONEZONE_IA", "INTELLIGENT_TIERING", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"], var.transition_storage_class)
    error_message = "transition_storage_class は STANDARD_IA / ONEZONE_IA / INTELLIGENT_TIERING / GLACIER_IR / GLACIER / DEEP_ARCHIVE のいずれかにすること。"
  }
}

variable "expiration_days" {
  description = "作成から何日後に現行バージョンを削除するか。null なら削除しない"
  type        = number
  default     = null
  validation {
    condition     = var.expiration_days == null || try(var.expiration_days >= 1 && floor(var.expiration_days) == var.expiration_days, false)
    error_message = "expiration_days は 1 以上の整数か null にすること。"
  }
}

variable "noncurrent_version_expiration_days" {
  description = "非現行になってから何日後に古いバージョンを削除するか（バージョニング有効時のみ意味を持つ）。null なら削除しない"
  type        = number
  default     = null
  validation {
    condition     = var.noncurrent_version_expiration_days == null || try(var.noncurrent_version_expiration_days >= 1 && floor(var.noncurrent_version_expiration_days) == var.noncurrent_version_expiration_days, false)
    error_message = "noncurrent_version_expiration_days は 1 以上の整数か null にすること。"
  }
}

variable "abort_incomplete_multipart_days" {
  description = "開始から何日後に未完了のマルチパートアップロードを中止するか（課金の取りこぼしを防ぐ）。null なら中止しない"
  type        = number
  default     = 7
  validation {
    condition     = var.abort_incomplete_multipart_days == null || try(var.abort_incomplete_multipart_days >= 1 && floor(var.abort_incomplete_multipart_days) == var.abort_incomplete_multipart_days, false)
    error_message = "abort_incomplete_multipart_days は 1 以上の整数か null にすること。"
  }
}
