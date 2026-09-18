# インターネットを経由せずにマネージドサービスへ接続する VPC エンドポイント。
# Gateway 型（S3 / DynamoDB）はルートテーブルに経路を足し、Interface 型はサブネットに ENI を置く。
# 型ごとに必要な入力が違うので、型に合わない入力は variable の validation で弾き、
# 型に無関係な属性は空にして渡す（null にすると computed 扱いで plan の差分が読みにくくなる）。

resource "aws_vpc_endpoint" "this" {
  vpc_id            = var.vpc_id
  service_name      = var.service_name
  vpc_endpoint_type = var.vpc_endpoint_type

  subnet_ids          = var.vpc_endpoint_type == "Interface" ? var.subnet_ids : []
  security_group_ids  = var.vpc_endpoint_type == "Interface" ? var.security_group_ids : []
  private_dns_enabled = var.vpc_endpoint_type == "Interface" ? var.private_dns_enabled : false

  route_table_ids = var.vpc_endpoint_type == "Gateway" ? var.route_table_ids : []

  tags = merge(var.tags, { Name = var.name })
}
