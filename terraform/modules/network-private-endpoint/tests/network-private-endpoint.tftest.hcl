mock_provider "aws" {}

variables {
  name   = "secretsmanager"
  vpc_id = "vpc-0123456789abcdef0"
  tags   = { env = "example" }
}

run "interface_endpoint" {
  command = plan
  variables {
    service_name       = "com.amazonaws.us-east-1.secretsmanager"
    vpc_endpoint_type  = "Interface"
    subnet_ids         = ["subnet-0123456789abcdef0", "subnet-0123456789abcdef1"]
    security_group_ids = ["sg-0123456789abcdef0"]
  }

  assert {
    condition     = aws_vpc_endpoint.this.vpc_endpoint_type == "Interface"
    error_message = "型は入力どおり"
  }
  assert {
    condition     = length(aws_vpc_endpoint.this.subnet_ids) == 2 && length(aws_vpc_endpoint.this.security_group_ids) == 1
    error_message = "Interface 型はサブネットと SG を持つ"
  }
  assert {
    condition     = contains(aws_vpc_endpoint.this.security_group_ids, "sg-0123456789abcdef0")
    error_message = "指定した SG を付ける"
  }
  assert {
    condition     = length(aws_vpc_endpoint.this.route_table_ids) == 0
    error_message = "Interface 型はルートテーブルを持たない"
  }
  assert {
    condition     = aws_vpc_endpoint.this.private_dns_enabled == true
    error_message = "Interface 型は既定でプライベート DNS を有効にする"
  }
  assert {
    condition     = aws_vpc_endpoint.this.tags["env"] == "example" && aws_vpc_endpoint.this.tags["Name"] == "secretsmanager"
    error_message = "tags と Name を付ける"
  }
}

run "interface_endpoint_without_private_dns" {
  command = plan
  variables {
    service_name        = "com.amazonaws.us-east-1.secretsmanager"
    vpc_endpoint_type   = "Interface"
    subnet_ids          = ["subnet-0123456789abcdef0"]
    security_group_ids  = ["sg-0123456789abcdef0"]
    private_dns_enabled = false
  }

  assert {
    condition     = aws_vpc_endpoint.this.private_dns_enabled == false
    error_message = "private_dns_enabled を無効にできる"
  }
}

run "gateway_endpoint" {
  command = plan
  variables {
    name              = "s3"
    service_name      = "com.amazonaws.us-east-1.s3"
    vpc_endpoint_type = "Gateway"
    route_table_ids   = ["rtb-0123456789abcdef0"]
  }

  assert {
    condition     = aws_vpc_endpoint.this.vpc_endpoint_type == "Gateway"
    error_message = "型は入力どおり"
  }
  assert {
    condition     = length(aws_vpc_endpoint.this.route_table_ids) == 1 && contains(aws_vpc_endpoint.this.route_table_ids, "rtb-0123456789abcdef0")
    error_message = "Gateway 型はルートテーブルに経路を足す"
  }
  assert {
    condition     = length(aws_vpc_endpoint.this.subnet_ids) == 0 && length(aws_vpc_endpoint.this.security_group_ids) == 0
    error_message = "Gateway 型はサブネットと SG を持たない"
  }
  assert {
    condition     = aws_vpc_endpoint.this.private_dns_enabled == false
    error_message = "Gateway 型はプライベート DNS を有効にしない"
  }
}

run "rejects_interface_without_security_group" {
  command = plan
  variables {
    service_name      = "com.amazonaws.us-east-1.secretsmanager"
    vpc_endpoint_type = "Interface"
    subnet_ids        = ["subnet-0123456789abcdef0"]
  }
  expect_failures = [var.security_group_ids]
}

run "rejects_interface_without_subnet" {
  command = plan
  variables {
    service_name       = "com.amazonaws.us-east-1.secretsmanager"
    vpc_endpoint_type  = "Interface"
    security_group_ids = ["sg-0123456789abcdef0"]
  }
  expect_failures = [var.subnet_ids]
}

run "rejects_gateway_without_route_table" {
  command = plan
  variables {
    service_name      = "com.amazonaws.us-east-1.s3"
    vpc_endpoint_type = "Gateway"
  }
  expect_failures = [var.route_table_ids]
}

run "rejects_gateway_with_subnet" {
  command = plan
  variables {
    service_name      = "com.amazonaws.us-east-1.s3"
    vpc_endpoint_type = "Gateway"
    route_table_ids   = ["rtb-0123456789abcdef0"]
    subnet_ids        = ["subnet-0123456789abcdef0"]
  }
  expect_failures = [var.subnet_ids]
}

run "rejects_unknown_type" {
  command = plan
  variables {
    service_name      = "com.amazonaws.us-east-1.s3"
    vpc_endpoint_type = "GatewayLoadBalancer"
  }
  expect_failures = [var.vpc_endpoint_type]
}
