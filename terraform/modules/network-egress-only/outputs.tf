output "route_table_id" {
  description = "既定経路を追加したルートテーブルの ID"
  value       = var.route_table_id
}

output "ipv4_route_id" {
  description = "IPv4 既定経路（0.0.0.0/0 → NAT）の ID。作らなければ null"
  value       = one(aws_route.ipv4[*].id)
}

output "ipv6_route_id" {
  description = "IPv6 既定経路（::/0 → Egress-only IGW）の ID。作らなければ null"
  value       = one(aws_route.ipv6[*].id)
}
