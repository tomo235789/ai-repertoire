variable "name" {
  description = "エンドポイントの Name タグ"
  type        = string

  validation {
    condition     = length(var.name) > 0
    error_message = "name は空にできない"
  }
}

variable "vpc_id" {
  description = "エンドポイントを置く VPC の ID"
  type        = string

  validation {
    condition     = can(regex("^vpc-[0-9a-f]+$", var.vpc_id))
    error_message = "vpc_id は vpc-xxxx の形式"
  }
}

variable "service_name" {
  description = "接続先サービス名（例 com.amazonaws.us-east-1.s3、com.amazonaws.us-east-1.secretsmanager）"
  type        = string

  validation {
    condition     = can(regex("^(com\\.amazonaws\\.|aws\\.sagemaker\\.|cn\\.com\\.amazonaws\\.)", var.service_name))
    error_message = "service_name は com.amazonaws.<region>.<service> の形式"
  }
}

variable "vpc_endpoint_type" {
  description = "Gateway（S3 / DynamoDB。ルートテーブルに経路を足す）か Interface（それ以外。サブネットに ENI を置く）"
  type        = string

  validation {
    condition     = contains(["Gateway", "Interface"], var.vpc_endpoint_type)
    error_message = "vpc_endpoint_type は Gateway か Interface"
  }
}

variable "subnet_ids" {
  description = "Interface 型で ENI を置くプライベートサブネットの ID。Gateway 型では指定しない"
  type        = list(string)
  default     = []

  validation {
    condition     = var.vpc_endpoint_type == "Interface" ? length(var.subnet_ids) > 0 : length(var.subnet_ids) == 0
    error_message = "Interface 型は subnet_ids が 1 つ以上必要、Gateway 型では指定できない"
  }
}

variable "security_group_ids" {
  description = "Interface 型の ENI に付けるセキュリティグループの ID（接続元からの 443 を許可したもの）。Gateway 型では指定しない"
  type        = list(string)
  default     = []

  validation {
    condition     = var.vpc_endpoint_type == "Interface" ? length(var.security_group_ids) > 0 : length(var.security_group_ids) == 0
    error_message = "Interface 型は security_group_ids が 1 つ以上必要、Gateway 型では指定できない"
  }
}

variable "route_table_ids" {
  description = "Gateway 型で経路を追加するルートテーブルの ID。Interface 型では指定しない"
  type        = list(string)
  default     = []

  validation {
    condition     = var.vpc_endpoint_type == "Gateway" ? length(var.route_table_ids) > 0 : length(var.route_table_ids) == 0
    error_message = "Gateway 型は route_table_ids が 1 つ以上必要、Interface 型では指定できない"
  }
}

variable "private_dns_enabled" {
  description = "Interface 型でサービスの既定 DNS 名をエンドポイントに向ける（SDK の設定変更なしでプライベート接続になる）。Gateway 型では無視する"
  type        = bool
  default     = true
}

variable "tags" {
  description = "全リソースに付けるタグ"
  type        = map(string)
  default     = {}
}
