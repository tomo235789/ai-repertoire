---
id: network-private-subnet
lang: terraform
title: インターネットから直接到達できないプライベートサブネットを作る
tags: [プライベートサブネット, ルートテーブル, 非公開, private-subnet, route-table, no-public-ip, vpc]
lib: hashicorp/aws
fn: aws_subnet
since: "5.0"
verified: 2026-09-18
status: public
---

パブリック IP を自動付与せず、IGW への経路を持たない専用ルートテーブルを関連付けたサブネットを作る。外向き通信が要るときは `route_table_id` を network-egress-only に渡す。

## Signature

```hcl
variables: name, vpc_id, cidr_block, availability_zone, tags = {}
outputs:   subnet_id, subnet_arn, route_table_id
```

## Usage

```hcl
module "private_a" {
  source            = "./modules/network-private-subnet"
  name              = "app-private-a"
  vpc_id            = "vpc-0123456789abcdef0"
  cidr_block        = "10.0.1.0/24"
  availability_zone = "us-east-1a"
  tags              = { env = "example" }
}
```

## Contract

- `map_public_ip_on_launch = false`。起動したインスタンス・タスクにパブリック IP が付かない
- サブネット専用の `aws_route_table` を作って関連付ける。VPC のメインルートテーブルは使わない
- ルートテーブルに IGW 向けの経路も既定経路（`0.0.0.0/0`、`::/0`）も持たない。VPC ローカル経路のみ
- `tags` を全リソースに付け、`Name` に `name` を入れる
- `vpc_id` は `vpc-` 形式、`cidr_block` は IPv4 CIDR でなければ validation で拒否

## Alternatives

- 外向き通信が必要なら network-egress-only で `route_table_id` に NAT ゲートウェイ / Egress-only IGW への既定経路を足す
- S3 / DynamoDB などへの接続だけなら NAT より network-private-endpoint（Gateway 型）が安く、インターネットを経由しない
- 複数 AZ に置くときはこの module を AZ ごとに `for_each` で呼ぶ（サブネットは 1 AZ に固定される）

## Pitfalls

- `cidr_block`、`availability_zone`、`vpc_id` の変更はサブネットの再作成になる。中のリソースを先に退避する
- ルートテーブルに `route` をインラインで書き足すと、network-egress-only の `aws_route` と競合して plan のたびに差分が出る。経路は必ず `aws_route` リソースで足す
- IPv6 は扱わない。IPv6 サブネットが必要なら `ipv6_cidr_block` と `assign_ipv6_address_on_creation` を別途設定する

## Test

`modules/network-private-subnet/tests/network-private-subnet.tftest.hcl`
