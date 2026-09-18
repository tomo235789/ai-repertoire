---
id: network-egress-only
lang: terraform
title: 外向き通信だけを許可するネットワーク経路を作る
tags: [外向き通信, NAT, 既定経路, egress-only, nat-gateway, default-route, ipv6]
lib: hashicorp/aws
fn: aws_route
since: "5.0"
verified: 2026-09-18
status: public
---

プライベートサブネットのルートテーブルに、NAT ゲートウェイ（IPv4）か Egress-only IGW（IPv6）への既定経路だけを足す。外から始まる接続は通らない。

## Signature

```hcl
variables: route_table_id, nat_gateway_id = null, egress_only_internet_gateway_id = null
outputs:   route_table_id, ipv4_route_id, ipv6_route_id
```

## Usage

```hcl
module "egress" {
  source         = "./modules/network-egress-only"
  route_table_id = module.private_a.route_table_id
  nat_gateway_id = "nat-0123456789abcdef0"
  # IPv6 も使うなら egress_only_internet_gateway_id = "eigw-..."
}
```

## Contract

- `nat_gateway_id` を渡すと `0.0.0.0/0 → NAT ゲートウェイ` の `aws_route` を 1 本、`egress_only_internet_gateway_id` を渡すと `::/0 → Egress-only IGW` を 1 本作る。両方なら 2 本
- インターネットゲートウェイ（`igw-`）への経路は作らない。`nat_gateway_id` に `igw-` を渡すと validation で拒否
- 両方 `null` は validation で拒否（何も作らない呼び出しを防ぐ）
- 作らなかった側の `*_route_id` 出力は `null`
- 既存のルートテーブルに経路を追加するだけで、ルートテーブル自体やサブネットには触らない
- `aws_route` は tags を持たないため `tags` variable は無い

## Alternatives

- AWS サービスへの通信だけなら NAT より network-private-endpoint が安く、インターネットを経由しない
- 複数 AZ で NAT ゲートウェイを AZ ごとに置くなら、ルートテーブルも AZ ごとに分けてこの module を AZ 数だけ呼ぶ
- IPv6 のみの環境なら NAT ゲートウェイは不要。Egress-only IGW だけで足りる

## Pitfalls

- `route_table_id` や宛先 CIDR の変更は経路の再作成になる（短時間の疎通断）
- 同じルートテーブルに `aws_route_table` のインライン `route` が書かれていると競合して差分が出続ける
- NAT ゲートウェイは AZ 障害の影響を受ける。別 AZ のサブネットから使うと AZ 間通信料も掛かる
- Egress-only IGW は IPv6 専用。IPv4 の `0.0.0.0/0` を向けることはできない

## Test

`modules/network-egress-only/tests/network-egress-only.tftest.hcl`
