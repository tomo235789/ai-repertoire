# 外向き通信だけを許可する既定経路。
# NAT ゲートウェイ / Egress-only IGW は外から始まる接続を通さないため、経路を足しても入向きは開かない。
# aws_route は tags を持たないので tags variable は無い。

resource "aws_route" "ipv4" {
  count = var.nat_gateway_id != null ? 1 : 0

  route_table_id         = var.route_table_id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = var.nat_gateway_id
}

resource "aws_route" "ipv6" {
  count = var.egress_only_internet_gateway_id != null ? 1 : 0

  route_table_id              = var.route_table_id
  destination_ipv6_cidr_block = "::/0"
  egress_only_gateway_id      = var.egress_only_internet_gateway_id
}
