# route は Optional+Computed のため plan では未知になる。mock の既定値を plan 時に適用して
# 「インラインの route が設定されていない（= IGW への経路が無い）」ことを検査できるようにする
mock_provider "aws" {
  override_during = plan
  mock_resource "aws_route_table" {
    defaults = {
      id    = "rtb-0123456789abcdef0"
      route = []
    }
  }
  mock_resource "aws_subnet" {
    defaults = {
      id = "subnet-0123456789abcdef0"
    }
  }
}

variables {
  name              = "app-private-a"
  vpc_id            = "vpc-0123456789abcdef0"
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  tags              = { env = "example" }
}

run "private_subnet" {
  command = plan

  assert {
    condition     = aws_subnet.this.map_public_ip_on_launch == false
    error_message = "パブリック IP を自動付与してはならない"
  }
  assert {
    condition     = aws_subnet.this.cidr_block == "10.0.1.0/24" && aws_subnet.this.availability_zone == "us-east-1a"
    error_message = "CIDR と AZ は入力どおり"
  }
  assert {
    condition     = length([for r in aws_route_table.this.route : r if r.gateway_id != null && r.gateway_id != ""]) == 0
    error_message = "ルートテーブルに IGW 向けの経路があってはならない"
  }
  assert {
    condition     = length([for r in aws_route_table.this.route : r if r.cidr_block == "0.0.0.0/0" || r.ipv6_cidr_block == "::/0"]) == 0
    error_message = "既定経路（0.0.0.0/0, ::/0）を持ってはならない"
  }
  assert {
    condition     = aws_route_table.this.vpc_id == var.vpc_id
    error_message = "ルートテーブルは同じ VPC に作る"
  }
  assert {
    condition     = aws_route_table_association.this.subnet_id == aws_subnet.this.id && aws_route_table_association.this.route_table_id == aws_route_table.this.id
    error_message = "専用ルートテーブルをサブネットに関連付ける"
  }
  assert {
    condition     = aws_subnet.this.tags["env"] == "example" && aws_subnet.this.tags["Name"] == "app-private-a"
    error_message = "サブネットに tags と Name を付ける"
  }
  assert {
    condition     = aws_route_table.this.tags["env"] == "example" && aws_route_table.this.tags["Name"] == "app-private-a"
    error_message = "ルートテーブルに tags と Name を付ける"
  }
}

run "rejects_invalid_vpc_id" {
  command = plan
  variables {
    vpc_id = "not-a-vpc"
  }
  expect_failures = [var.vpc_id]
}

run "rejects_invalid_cidr" {
  command = plan
  variables {
    cidr_block = "10.0.1.0"
  }
  expect_failures = [var.cidr_block]
}
