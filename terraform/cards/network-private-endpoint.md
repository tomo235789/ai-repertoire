---
id: network-private-endpoint
lang: terraform
title: インターネットを経由せずにマネージドサービスへ接続する
tags: [VPC エンドポイント, プライベート接続, PrivateLink, vpc-endpoint, private-link, gateway-endpoint, interface-endpoint]
lib: hashicorp/aws
fn: aws_vpc_endpoint
since: "5.0"
verified: 2026-09-18
status: public
---

S3 / DynamoDB は Gateway 型（ルートテーブルに経路を足す）、それ以外は Interface 型（サブネットに ENI を置く）の VPC エンドポイントを作る。型に合わない入力は validation で弾く。

## Signature

```hcl
variables: name, vpc_id, service_name, vpc_endpoint_type = "Gateway" | "Interface", subnet_ids = [], security_group_ids = [], route_table_ids = [], private_dns_enabled = true, tags = {}
outputs:   endpoint_id, endpoint_arn, dns_entries
```

## Usage

```hcl
module "secretsmanager_endpoint" {
  source             = "./modules/network-private-endpoint"
  name               = "secretsmanager"
  vpc_id             = "vpc-0123456789abcdef0"
  service_name       = "com.amazonaws.us-east-1.secretsmanager"
  vpc_endpoint_type  = "Interface"
  subnet_ids         = [module.private_a.subnet_id]
  security_group_ids = [module.endpoint_sg.security_group_id]
}
```

## Contract

- Interface 型は `subnet_ids` と `security_group_ids` が 1 つ以上必須、`route_table_ids` は指定不可。validation で拒否
- Gateway 型は `route_table_ids` が 1 つ以上必須、`subnet_ids` / `security_group_ids` は指定不可。validation で拒否
- Interface 型は既定で `private_dns_enabled = true`（サービスの既定 DNS 名がエンドポイントに向き、SDK の設定変更なしでプライベート接続になる）。Gateway 型では常に `false`
- `vpc_endpoint_type` は `Gateway` / `Interface` のみ。`service_name` は `com.amazonaws.` 形式のみ
- `tags` を付け、`Name` に `name` を入れる
- エンドポイントポリシーは設定しない（フルアクセス）。絞るなら `policy` を別途足す

## Alternatives

- S3 / DynamoDB は Gateway 型が無料。Interface 型（S3 の PrivateLink）はオンプレや別 VPC から使うときだけ
- 多数のサービスに Interface 型を並べるとコストが積み上がる。NAT ゲートウェイ経由で十分な場合もある（ただしインターネットを経由する）
- 接続元 SG から 443 を許可した `security_group_ids` は network-security-group-minimal で作る

## Pitfalls

- `service_name`、`vpc_endpoint_type`、`vpc_id` の変更は再作成になる
- Interface 型で `private_dns_enabled = true` にするには VPC の `enable_dns_support` と `enable_dns_hostnames` が両方 true でないと apply が失敗する
- `service_name` のリージョンは VPC のリージョンと一致させる。別リージョンのサービス名は作成に失敗する
- Gateway 型は同じ VPC のルートテーブルにしか経路を足せない。VPC ピアリング越しには使えない

## Test

`modules/network-private-endpoint/tests/network-private-endpoint.tftest.hcl`
