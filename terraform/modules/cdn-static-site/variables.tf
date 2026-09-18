variable "bucket_name" {
  description = "配信元の S3 バケット名（このモジュールは作らない。storage-bucket-private で作ったものを渡す）"
  type        = string
  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$", var.bucket_name))
    error_message = "bucket_name は S3 のバケット命名規則に従うこと。"
  }
}

variable "bucket_regional_domain_name" {
  description = "配信元バケットのリージョン別ドメイン名（例: example-bucket.s3.us-east-1.amazonaws.com）"
  type        = string
}

variable "certificate_arn" {
  description = "ACM 証明書の ARN。CloudFront は us-east-1 の証明書しか使えない"
  type        = string
  validation {
    condition     = can(regex("^arn:aws[a-z-]*:acm:us-east-1:[0-9]{12}:certificate/", var.certificate_arn))
    error_message = "certificate_arn は us-east-1 の ACM 証明書の ARN にすること（CloudFront の制約）。"
  }
}

variable "aliases" {
  description = "配信に使う独自ドメイン名。証明書がカバーしている名前だけを渡す"
  type        = list(string)
  validation {
    condition     = length(var.aliases) > 0
    error_message = "aliases は 1 つ以上指定すること。"
  }
}

variable "default_root_object" {
  description = "ルートへのアクセスで返すオブジェクト"
  type        = string
  default     = "index.html"
}

variable "price_class" {
  description = "エッジロケーションの範囲。PriceClass_100 / PriceClass_200 / PriceClass_All"
  type        = string
  default     = "PriceClass_100"
  validation {
    condition     = contains(["PriceClass_100", "PriceClass_200", "PriceClass_All"], var.price_class)
    error_message = "price_class は PriceClass_100 / PriceClass_200 / PriceClass_All のいずれかにすること。"
  }
}

variable "tags" {
  description = "全リソースに付けるタグ"
  type        = map(string)
  default     = {}
}
