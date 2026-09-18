---
id: network-egress-only
lang: aws
title: 外向き通信だけを許可するネットワーク経路を作る
tags: [外向き, NAT, 経路, ルート, egress, nat gateway, route, ipv6]
lib: aws.ec2
fn: egress_only_route
since: "2024"
verified: 2026-09-18
status: public
---

プライベートサブネットのルートテーブルに、IPv4 は NAT Gateway、IPv6 は Egress-only IGW への既定経路を足す。出力は boto3 `ec2.create_route` の kwargs のリスト。

## Signature

```python
egress_only_route(route_table_id: str, nat_gateway_id: str | None = None, egress_only_igw_id: str | None = None) -> list[dict]
```

## Usage

```python
from importlib import import_module

egress_only_route = import_module("network-egress-only").egress_only_route
routes = egress_only_route("rtb-0abc", nat_gateway_id="nat-0abc", egress_only_igw_id="eigw-0abc")
# => [{"RouteTableId": "rtb-0abc", "DestinationCidrBlock": "0.0.0.0/0", "NatGatewayId": "nat-0abc"},
#     {"RouteTableId": "rtb-0abc", "DestinationIpv6CidrBlock": "::/0", "EgressOnlyInternetGatewayId": "eigw-0abc"}]
# for r in routes: ec2.create_route(**r)
```

## Contract

- 副作用無し。同じ入力から同じ出力。出力は `json.dumps` できる
- 渡した ID の分だけ経路を返す。`nat_gateway_id` は `0.0.0.0/0` → `NatGatewayId`、`egress_only_igw_id` は `::/0` → `EgressOnlyInternetGatewayId`
- 両方 `None` なら `ValueError`
- 入向きの経路は作らない。出力に `GatewayId`（Internet Gateway）は含まれず、`igw-` 始まりの ID を渡すと `ValueError`
- `route_table_id` は `rtb-`、`nat_gateway_id` は `nat-`、`egress_only_igw_id` は `eigw-` 始まりでなければ `ValueError`

## Alternatives

- Terraform: `terraform/modules/network-egress-only`（同じ ID。`aws_route` を IPv4 / IPv6 で 1 つずつ）
- CloudFormation: `AWS::EC2::Route`（`NatGatewayId` / `EgressOnlyInternetGatewayId`）
- NAT Gateway の時間・転送課金を避けたい場合、S3 / DynamoDB は network-private-endpoint（Gateway 型）で経路を分ける。特定 AWS サービスだけなら Interface 型エンドポイントで NAT 自体を不要にできる

## Pitfalls

- NAT Gateway は AZ 単位。別 AZ のサブネットからも使えるが AZ 障害で巻き込まれ、AZ 間転送料金もかかる。AZ ごとに NAT を置き、AZ ごとのルートテーブルにこの関数を適用する
- NAT Gateway は IPv4 専用（NAT64 を有効化しない限り IPv6 は通らない）。IPv6 の外向きは Egress-only IGW が必要
- 同じ宛先（`0.0.0.0/0`）の経路が既にあると `create_route` は `RouteAlreadyExists` で失敗する。置き換えは `replace_route`
- NAT Gateway 自体はパブリックサブネットに置く。この関数はプライベート側のルートテーブルにしか触らない

## Test

`examples/network-egress-only_test.py`
