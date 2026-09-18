variable "name" {
  description = "セキュリティグループ名（変更すると再作成）"
  type        = string

  validation {
    condition     = length(var.name) > 0 && length(var.name) <= 255
    error_message = "name は 1〜255 文字"
  }
}

variable "description" {
  description = "セキュリティグループの説明（必須。変更すると再作成）"
  type        = string

  validation {
    condition     = length(trimspace(var.description)) > 0
    error_message = "description は空にできない"
  }
}

variable "vpc_id" {
  description = "セキュリティグループを置く VPC の ID"
  type        = string

  validation {
    condition     = can(regex("^vpc-[0-9a-f]+$", var.vpc_id))
    error_message = "vpc_id は vpc-xxxx の形式"
  }
}

variable "ingress_rules" {
  description = "許可する入向き規則。cidr（IPv4 / IPv6）か source_security_group_id のどちらか一方を指定し、description を必ず付ける"
  type = list(object({
    port                     = number
    protocol                 = optional(string, "tcp")
    cidr                     = optional(string)
    source_security_group_id = optional(string)
    description              = string
  }))
  default = []

  validation {
    condition     = alltrue([for r in var.ingress_rules : (r.cidr != null) != (r.source_security_group_id != null)])
    error_message = "各規則は cidr と source_security_group_id のどちらか一方だけを指定する"
  }

  validation {
    condition = alltrue([
      for r in var.ingress_rules :
      !(contains(["0.0.0.0/0", "::/0"], coalesce(r.cidr, "-")) && contains([22, 3389], r.port))
    ])
    error_message = "SSH(22) と RDP(3389) を全世界（0.0.0.0/0, ::/0）に開けてはならない"
  }

  validation {
    condition     = alltrue([for r in var.ingress_rules : r.port >= 0 && r.port <= 65535 && floor(r.port) == r.port])
    error_message = "port は 0〜65535 の整数"
  }

  validation {
    condition     = alltrue([for r in var.ingress_rules : contains(["tcp", "udp"], r.protocol)])
    error_message = "protocol は tcp か udp"
  }

  validation {
    condition     = alltrue([for r in var.ingress_rules : length(trimspace(r.description)) > 0])
    error_message = "各規則に description を付ける"
  }

  validation {
    condition = alltrue([
      for r in var.ingress_rules :
      r.cidr == null || can(cidrnetmask(r.cidr)) || can(cidrhost(r.cidr, 0))
    ])
    error_message = "cidr は IPv4 / IPv6 の CIDR 表記"
  }
}

variable "allow_all_egress" {
  description = "外向き通信を全許可するか。false にすると外向き規則を作らず、すべての外向き通信を拒否する（既定は true）"
  type        = bool
  default     = true
}

variable "tags" {
  description = "全リソースに付けるタグ"
  type        = map(string)
  default     = {}
}
