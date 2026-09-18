# インターネットから直接到達できないプライベートサブネット。
# パブリック IP を自動付与せず、IGW への経路を持たない専用ルートテーブルを関連付ける。
# 外向き通信が必要なら network-egress-only でこのルートテーブルに NAT / Egress-only IGW への既定経路を足す。

resource "aws_subnet" "this" {
  vpc_id                  = var.vpc_id
  cidr_block              = var.cidr_block
  availability_zone       = var.availability_zone
  map_public_ip_on_launch = false

  tags = merge(var.tags, { Name = var.name })
}

# route ブロックをインラインで持たない（= VPC ローカル経路のみ）。IGW への経路はこの module では作らない
resource "aws_route_table" "this" {
  vpc_id = var.vpc_id

  tags = merge(var.tags, { Name = var.name })
}

resource "aws_route_table_association" "this" {
  subnet_id      = aws_subnet.this.id
  route_table_id = aws_route_table.this.id
}
