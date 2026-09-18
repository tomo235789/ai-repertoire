variable "name" {
  description = "サブネットとルートテーブルの Name タグ"
  type        = string

  validation {
    condition     = length(var.name) > 0
    error_message = "name は空にできない"
  }
}

variable "vpc_id" {
  description = "サブネットを置く VPC の ID"
  type        = string

  validation {
    condition     = can(regex("^vpc-[0-9a-f]+$", var.vpc_id))
    error_message = "vpc_id は vpc-xxxx の形式"
  }
}

variable "cidr_block" {
  description = "サブネットの IPv4 CIDR（VPC の CIDR に含まれること）"
  type        = string

  validation {
    condition     = can(cidrnetmask(var.cidr_block))
    error_message = "cidr_block は IPv4 CIDR（例 10.0.1.0/24）"
  }
}

variable "availability_zone" {
  description = "サブネットを置くアベイラビリティゾーン（例 us-east-1a）"
  type        = string

  validation {
    condition     = length(var.availability_zone) > 0
    error_message = "availability_zone は空にできない"
  }
}

variable "tags" {
  description = "全リソースに付けるタグ"
  type        = map(string)
  default     = {}
}
