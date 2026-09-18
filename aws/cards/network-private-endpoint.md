---
id: network-private-endpoint
lang: aws
title: インターネットを経由せずにマネージドサービスへ接続する
tags: [エンドポイント, PrivateLink, VPC, endpoint, privatelink, interface, gateway, ec2]
lib: aws.ec2
fn: private_endpoint
since: "2024"
verified: 2026-09-18
status: public
---

Interface 型（PrivateLink）か Gateway 型（S3 / DynamoDB）の VPC エンドポイントを組み立てる。出力は boto3 `ec2.create_vpc_endpoint` の kwargs。

## Signature

```python
private_endpoint(vpc_id: str, service_name: str, endpoint_type: str, subnet_ids: list[str] | None = None, security_group_ids: list[str] | None = None, route_table_ids: list[str] | None = None) -> dict
```

## Usage

```python
from importlib import import_module

private_endpoint = import_module("network-private-endpoint").private_endpoint
sm = private_endpoint("vpc-0abc", "com.amazonaws.us-east-1.secretsmanager", "Interface",
                      subnet_ids=["subnet-0a", "subnet-0b"], security_group_ids=["sg-0abc"])
# => {..., "VpcEndpointType": "Interface", "SubnetIds": [...], "SecurityGroupIds": [...], "PrivateDnsEnabled": True}
s3 = private_endpoint("vpc-0abc", "com.amazonaws.us-east-1.s3", "Gateway", route_table_ids=["rtb-0abc"])
# => {..., "VpcEndpointType": "Gateway", "RouteTableIds": ["rtb-0abc"]}   ec2.create_vpc_endpoint(**s3)
```

## Contract

- 副作用無し。同じ入力から同じ出力。出力のリストは引数と別オブジェクト。出力は `json.dumps` できる
- `Interface`: `subnet_ids` と `security_group_ids` が 1 つ以上必須、`PrivateDnsEnabled: True` を付ける。`route_table_ids` を渡すと `ValueError`
- `Gateway`: `route_table_ids` が 1 つ以上必須、`PrivateDnsEnabled` は付けない。`subnet_ids` / `security_group_ids` を渡すと `ValueError`
- `Gateway` は `service_name` の末尾が `s3` か `dynamodb` でなければ `ValueError`
- `endpoint_type` が `Interface` / `Gateway` 以外（`GatewayLoadBalancer` 含む）、`service_name` が空か `.` を含まない、ID の接頭辞（`vpc-` / `subnet-` / `sg-` / `rtb-`）違いは `ValueError`

## Alternatives

- Terraform: `terraform/modules/network-private-endpoint`（同じ ID。`aws_vpc_endpoint`）
- CloudFormation: `AWS::EC2::VPCEndpoint`
- S3 / DynamoDB は Gateway 型が無料。Interface 型は時間 + 転送課金なので、NAT 経由の転送量と比べて選ぶ

## Pitfalls

- `service_name` のリージョンは VPC のリージョンと一致させる。別リージョンの名前は `InvalidServiceName`
- `PrivateDnsEnabled: True` は VPC の `enableDnsSupport` と `enableDnsHostnames` が両方 true でないと失敗する
- Interface 型の SG は 443 の ingress を利用側（ECS / Lambda の SG）から許可する必要がある。network-security-group-minimal で `source_sg` を使う
- ECR は `ecr.api` と `ecr.dkr` の 2 つ + S3 Gateway が必要。1 つでは pull できない
- `VpcEndpointType` と `ServiceName` は作成後に変更できない。サブネット / SG / ルートテーブルは `modify_vpc_endpoint` で変えられる

## Test

`examples/network-private-endpoint_test.py`
