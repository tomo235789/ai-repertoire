variable "name" {
  description = "バケット名。グローバルに一意で、3〜63 文字の小文字英数字・ハイフン・ドット（変更すると再作成）"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.name)) && !can(regex("[.]{2}|[.]-|-[.]", var.name))
    error_message = "name は S3 のバケット命名規則（3〜63 文字、小文字英数字・ハイフン・ドット、先頭末尾は英数字）に従うこと。"
  }
}

variable "kms_key_arn" {
  description = "保存時暗号化に使う顧客管理 KMS キーの ARN。null なら SSE-S3（AES256）"
  type        = string
  default     = null
  validation {
    condition     = var.kms_key_arn == null || can(regex("^arn:aws[a-z-]*:kms:", var.kms_key_arn))
    error_message = "kms_key_arn は KMS キーの ARN（arn:aws:kms:...）か null にすること。"
  }
}

variable "force_destroy" {
  description = "true にすると destroy 時にオブジェクトごと削除する。既定は false（オブジェクトが残っていれば destroy が失敗する）"
  type        = bool
  default     = false
}

variable "tags" {
  description = "全リソースに付けるタグ"
  type        = map(string)
  default     = {}
}
