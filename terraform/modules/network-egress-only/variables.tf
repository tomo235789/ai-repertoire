variable "route_table_id" {
  description = "既定経路を追加するルートテーブルの ID（network-private-subnet の route_table_id）"
  type        = string

  validation {
    condition     = can(regex("^rtb-[0-9a-f]+$", var.route_table_id))
    error_message = "route_table_id は rtb-xxxx の形式"
  }
}

variable "nat_gateway_id" {
  description = "IPv4 の外向き既定経路（0.0.0.0/0）を向ける NAT ゲートウェイの ID。IPv4 の外向き通信が不要なら null"
  type        = string
  default     = null

  validation {
    condition     = var.nat_gateway_id == null || can(regex("^nat-[0-9a-f]+$", var.nat_gateway_id))
    error_message = "nat_gateway_id は nat-xxxx の形式"
  }

  validation {
    condition     = var.nat_gateway_id != null || var.egress_only_internet_gateway_id != null
    error_message = "nat_gateway_id と egress_only_internet_gateway_id の少なくとも一方を指定する"
  }
}

variable "egress_only_internet_gateway_id" {
  description = "IPv6 の外向き既定経路（::/0）を向ける Egress-only インターネットゲートウェイの ID。IPv6 を使わないなら null"
  type        = string
  default     = null

  validation {
    condition     = var.egress_only_internet_gateway_id == null || can(regex("^eigw-[0-9a-f]+$", var.egress_only_internet_gateway_id))
    error_message = "egress_only_internet_gateway_id は eigw-xxxx の形式"
  }
}
