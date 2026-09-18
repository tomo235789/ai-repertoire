mock_provider "aws" {}

variables {
  name        = "app-web"
  description = "app の HTTPS と DB 接続だけを許可"
  vpc_id      = "vpc-0123456789abcdef0"
  tags        = { env = "example" }
  ingress_rules = [
    { port = 443, cidr = "10.0.0.0/16", description = "VPC 内からの HTTPS" },
    { port = 5432, source_security_group_id = "sg-0123456789abcdef0", description = "アプリ SG からの PostgreSQL" },
  ]
}

run "minimal_rules_without_egress" {
  command = plan
  variables {
    allow_all_egress = false
  }

  assert {
    condition     = length(aws_vpc_security_group_ingress_rule.this) == 2
    error_message = "指定した規則の数だけ入向き規則を作る"
  }
  assert {
    condition = (
      aws_vpc_security_group_ingress_rule.this["tcp-443-10.0.0.0/16"].cidr_ipv4 == "10.0.0.0/16"
      && aws_vpc_security_group_ingress_rule.this["tcp-443-10.0.0.0/16"].from_port == 443
      && aws_vpc_security_group_ingress_rule.this["tcp-443-10.0.0.0/16"].to_port == 443
      && aws_vpc_security_group_ingress_rule.this["tcp-443-10.0.0.0/16"].ip_protocol == "tcp"
    )
    error_message = "CIDR 規則は単一ポート・指定プロトコルで cidr_ipv4 に入る"
  }
  assert {
    condition     = aws_vpc_security_group_ingress_rule.this["tcp-443-10.0.0.0/16"].cidr_ipv6 == null && aws_vpc_security_group_ingress_rule.this["tcp-443-10.0.0.0/16"].referenced_security_group_id == null
    error_message = "IPv4 規則は cidr_ipv6 と参照 SG を持たない"
  }
  assert {
    condition     = aws_vpc_security_group_ingress_rule.this["tcp-5432-sg-0123456789abcdef0"].referenced_security_group_id == "sg-0123456789abcdef0" && aws_vpc_security_group_ingress_rule.this["tcp-5432-sg-0123456789abcdef0"].cidr_ipv4 == null
    error_message = "SG 参照規則は referenced_security_group_id に入り cidr を持たない"
  }
  assert {
    condition     = alltrue([for r in aws_vpc_security_group_ingress_rule.this : length(r.description) > 0])
    error_message = "全ての入向き規則に description がある"
  }
  assert {
    condition     = length(aws_vpc_security_group_egress_rule.all_ipv4) == 0 && length(aws_vpc_security_group_egress_rule.all_ipv6) == 0
    error_message = "allow_all_egress = false なら外向き規則を作らない"
  }
  assert {
    condition     = aws_security_group.this.name == "app-web" && aws_security_group.this.description == "app の HTTPS と DB 接続だけを許可"
    error_message = "name と description は入力どおり"
  }
  assert {
    condition     = aws_security_group.this.tags["env"] == "example" && alltrue([for r in aws_vpc_security_group_ingress_rule.this : r.tags["env"] == "example"])
    error_message = "SG と規則に tags を付ける"
  }
}

run "default_allows_all_egress" {
  command = plan

  assert {
    condition     = length(aws_vpc_security_group_egress_rule.all_ipv4) == 1 && length(aws_vpc_security_group_egress_rule.all_ipv6) == 1
    error_message = "既定では IPv4 / IPv6 の全許可外向き規則を 1 つずつ作る"
  }
  assert {
    condition     = aws_vpc_security_group_egress_rule.all_ipv4[0].ip_protocol == "-1" && aws_vpc_security_group_egress_rule.all_ipv4[0].cidr_ipv4 == "0.0.0.0/0"
    error_message = "IPv4 の外向きは全プロトコル・0.0.0.0/0"
  }
  assert {
    condition     = aws_vpc_security_group_egress_rule.all_ipv6[0].ip_protocol == "-1" && aws_vpc_security_group_egress_rule.all_ipv6[0].cidr_ipv6 == "::/0"
    error_message = "IPv6 の外向きは全プロトコル・::/0"
  }
}

run "ipv6_cidr_and_udp" {
  command = plan
  variables {
    ingress_rules = [
      { port = 53, protocol = "udp", cidr = "2001:db8::/32", description = "IPv6 からの DNS" },
    ]
  }

  assert {
    condition     = aws_vpc_security_group_ingress_rule.this["udp-53-2001:db8::/32"].cidr_ipv6 == "2001:db8::/32" && aws_vpc_security_group_ingress_rule.this["udp-53-2001:db8::/32"].cidr_ipv4 == null
    error_message = "IPv6 CIDR は cidr_ipv6 に入る"
  }
  assert {
    condition     = aws_vpc_security_group_ingress_rule.this["udp-53-2001:db8::/32"].ip_protocol == "udp"
    error_message = "protocol を指定できる"
  }
}

run "rejects_ssh_open_to_world" {
  command = plan
  variables {
    ingress_rules = [
      { port = 22, cidr = "0.0.0.0/0", description = "SSH" },
    ]
  }
  expect_failures = [var.ingress_rules]
}

run "rejects_rdp_open_to_world_ipv6" {
  command = plan
  variables {
    ingress_rules = [
      { port = 3389, cidr = "::/0", description = "RDP" },
    ]
  }
  expect_failures = [var.ingress_rules]
}

run "rejects_rule_without_description" {
  command = plan
  variables {
    ingress_rules = [
      { port = 443, cidr = "10.0.0.0/16", description = " " },
    ]
  }
  expect_failures = [var.ingress_rules]
}

run "rejects_both_cidr_and_source_sg" {
  command = plan
  variables {
    ingress_rules = [
      { port = 443, cidr = "10.0.0.0/16", source_security_group_id = "sg-0123456789abcdef0", description = "両方" },
    ]
  }
  expect_failures = [var.ingress_rules]
}

run "rejects_neither_cidr_nor_source_sg" {
  command = plan
  variables {
    ingress_rules = [
      { port = 443, description = "送信元なし" },
    ]
  }
  expect_failures = [var.ingress_rules]
}

run "rejects_empty_description" {
  command = plan
  variables {
    description = ""
  }
  expect_failures = [var.description]
}
