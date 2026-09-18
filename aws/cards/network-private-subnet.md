---
id: network-private-subnet
lang: aws
title: インターネットから直接到達できないプライベートサブネットを作る
tags: [サブネット, プライベート, VPC, subnet, private, vpc, ec2, route table]
lib: aws.ec2
fn: private_subnet
since: "2024"
verified: 2026-09-18
status: public
---

パブリック IP を自動付与せず、IGW への経路を持たない専用ルートテーブル付きのサブネットを組み立てる。出力は boto3 `ec2` の kwargs。

## Signature

```python
private_subnet(vpc_id: str, cidr: str, az: str, tags: dict[str, str], vpc_cidr: str | None = None) -> dict
```

## Usage

```python
from importlib import import_module

private_subnet = import_module("network-private-subnet").private_subnet
cfg = private_subnet("vpc-0abc", "10.0.1.0/24", "us-east-1a", {"Name": "app-private-a"}, vpc_cidr="10.0.0.0/16")
# cfg["create_subnet"]            -> ec2.create_subnet(**...)
# cfg["modify_subnet_attribute"]  -> {"MapPublicIpOnLaunch": {"Value": False}}（SubnetId を足して渡す）
# cfg["route_table"]              -> ec2.create_route_table(**...)（IGW への経路無し）
```

## Contract

- 副作用無し。同じ入力から同じ出力を返し、引数の `tags` を変更しない。出力は `json.dumps` できる
- `create_subnet` に `MapPublicIpOnLaunch` を含めず、`modify_subnet_attribute` で `{"Value": False}` を明示する（パブリック IP の自動付与無し）
- `route_table` は `create_route_table` の kwargs で、`GatewayId` や `0.0.0.0/0` を含まない（VPC ローカル経路のみ）。外向き通信は network-egress-only で足す
- `cidr` は `ipaddress` で検証し、ホストビット付き・プレフィックス無し・/16〜/28 の範囲外・IPv6・不正文字列は `ValueError`
- `vpc_cidr` を渡した場合、`cidr` が含まれなければ `ValueError`（渡さなければ包含は検証しない）
- `vpc_id` が `vpc-` 始まりでない、`az` が空、`tags` が空のときは `ValueError`
- `tags` は `TagSpecifications` としてサブネットとルートテーブルの両方に同じ内容で付く

## Alternatives

- Terraform: `terraform/modules/network-private-subnet`（同じ ID。`aws_subnet` + `aws_route_table` + association）
- CloudFormation: `AWS::EC2::Subnet`（`MapPublicIpOnLaunch: false`）+ `AWS::EC2::RouteTable` + `AWS::EC2::SubnetRouteTableAssociation`
- IPv6 専用 / デュアルスタックのサブネットは対象外（`Ipv6CidrBlock` を自分で足す）

## Pitfalls

- `CidrBlock` と `AvailabilityZone` は作成後に変更できない。CIDR を変えるにはサブネットを作り直す
- `modify_subnet_attribute` の kwargs には `SubnetId` が無い。`create_subnet` の応答 `Subnet.SubnetId` を足して呼ぶ。ルートテーブルも `associate_route_table(SubnetId=..., RouteTableId=...)` を別途呼ばないと VPC のメインルートテーブル（IGW 経路を持つことがある）に紐づく
- AZ 名（`us-east-1a`）はアカウントごとに物理 AZ への割り当てが違う。複数アカウントで揃えるなら AZ ID（`use1-az1`）を `AvailabilityZoneId` で使う
- 既定のセキュリティグループや NACL はこの関数の範囲外。NACL は VPC 既定の全許可のまま

## Test

`examples/network-private-subnet_test.py`
