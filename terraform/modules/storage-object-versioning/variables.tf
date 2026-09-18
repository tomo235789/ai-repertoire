variable "bucket_name" {
  description = "バージョニングを有効にするバケット名（aws_s3_bucket の id）"
  type        = string
  validation {
    condition     = length(var.bucket_name) >= 3
    error_message = "bucket_name は 3 文字以上のバケット名にすること。"
  }
}

variable "mfa_delete" {
  description = "true なら削除とバージョニング停止に MFA を必須にする（ルートユーザーの MFA デバイスが要る）"
  type        = bool
  default     = false
}

variable "mfa" {
  description = "mfa_delete = true のときに必要。MFA デバイスのシリアル番号と現在のコードをスペース区切りにした文字列"
  type        = string
  default     = null
  sensitive   = true
}
