# 必要なポートだけを開けるセキュリティグループ。
# 規則はインラインではなく aws_vpc_security_group_*_rule で持つ（インラインと混在させると差分が出続ける）。
# aws_security_group はインライン egress が無いと AWS が自動で作る全許可の外向き規則を削除するため、
# allow_all_egress = false のときは外向き通信が全て拒否される。

locals {
  ingress_by_key = {
    for r in var.ingress_rules :
    "${r.protocol}-${r.port}-${coalesce(r.cidr, r.source_security_group_id)}" => r
  }
}

resource "aws_security_group" "this" {
  name        = var.name
  description = var.description
  vpc_id      = var.vpc_id

  tags = merge(var.tags, { Name = var.name })

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_vpc_security_group_ingress_rule" "this" {
  for_each = local.ingress_by_key

  security_group_id = aws_security_group.this.id
  description       = each.value.description
  ip_protocol       = each.value.protocol
  from_port         = each.value.port
  to_port           = each.value.port

  # cidrnetmask は IPv4 だけを受け付けるので、これで IPv4 / IPv6 を振り分ける
  cidr_ipv4                    = each.value.cidr != null && can(cidrnetmask(each.value.cidr)) ? each.value.cidr : null
  cidr_ipv6                    = each.value.cidr != null && !can(cidrnetmask(each.value.cidr)) ? each.value.cidr : null
  referenced_security_group_id = each.value.source_security_group_id

  tags = var.tags
}

resource "aws_vpc_security_group_egress_rule" "all_ipv4" {
  count = var.allow_all_egress ? 1 : 0

  security_group_id = aws_security_group.this.id
  description       = "すべての外向き通信を許可（IPv4）"
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"

  tags = var.tags
}

resource "aws_vpc_security_group_egress_rule" "all_ipv6" {
  count = var.allow_all_egress ? 1 : 0

  security_group_id = aws_security_group.this.id
  description       = "すべての外向き通信を許可（IPv6）"
  ip_protocol       = "-1"
  cidr_ipv6         = "::/0"

  tags = var.tags
}
