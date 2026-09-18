mock_provider "aws" {}

variables {
  route_table_id = "rtb-0123456789abcdef0"
}

run "ipv4_via_nat" {
  command = plan
  variables {
    nat_gateway_id = "nat-0123456789abcdef0"
  }

  assert {
    condition     = length(aws_route.ipv4) == 1 && length(aws_route.ipv6) == 0
    error_message = "NAT だけを指定したら IPv4 の経路だけを作る"
  }
  assert {
    condition     = aws_route.ipv4[0].destination_cidr_block == "0.0.0.0/0"
    error_message = "IPv4 の既定経路は 0.0.0.0/0"
  }
  assert {
    condition     = aws_route.ipv4[0].nat_gateway_id == "nat-0123456789abcdef0"
    error_message = "IPv4 の既定経路は NAT ゲートウェイに向ける"
  }
  assert {
    condition     = aws_route.ipv4[0].route_table_id == "rtb-0123456789abcdef0"
    error_message = "指定したルートテーブルに追加する"
  }
  assert {
    condition     = output.ipv6_route_id == null
    error_message = "作らなかった経路の出力は null"
  }
}

run "ipv6_via_egress_only_igw" {
  command = plan
  variables {
    egress_only_internet_gateway_id = "eigw-0123456789abcdef0"
  }

  assert {
    condition     = length(aws_route.ipv4) == 0 && length(aws_route.ipv6) == 1
    error_message = "Egress-only IGW だけを指定したら IPv6 の経路だけを作る"
  }
  assert {
    condition     = aws_route.ipv6[0].destination_ipv6_cidr_block == "::/0"
    error_message = "IPv6 の既定経路は ::/0"
  }
  assert {
    condition     = aws_route.ipv6[0].egress_only_gateway_id == "eigw-0123456789abcdef0"
    error_message = "IPv6 の既定経路は Egress-only IGW に向ける"
  }
  assert {
    condition     = output.ipv4_route_id == null
    error_message = "作らなかった経路の出力は null"
  }
}

run "dual_stack" {
  command = plan
  variables {
    nat_gateway_id                  = "nat-0123456789abcdef0"
    egress_only_internet_gateway_id = "eigw-0123456789abcdef0"
  }

  assert {
    condition     = length(aws_route.ipv4) == 1 && length(aws_route.ipv6) == 1
    error_message = "両方を指定したら 2 本の経路を作る"
  }
  assert {
    condition     = output.route_table_id == "rtb-0123456789abcdef0"
    error_message = "route_table_id を出力する"
  }
}

run "rejects_no_gateway" {
  command         = plan
  expect_failures = [var.nat_gateway_id]
}

run "rejects_internet_gateway_id" {
  command = plan
  variables {
    nat_gateway_id = "igw-0123456789abcdef0"
  }
  expect_failures = [var.nat_gateway_id]
}

run "rejects_invalid_route_table_id" {
  command = plan
  variables {
    route_table_id = "vpc-0123456789abcdef0"
    nat_gateway_id = "nat-0123456789abcdef0"
  }
  expect_failures = [var.route_table_id]
}
