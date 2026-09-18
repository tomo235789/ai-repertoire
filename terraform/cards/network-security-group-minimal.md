---
id: network-security-group-minimal
lang: terraform
title: 必要なポートだけを開けるファイアウォール規則を作る
tags: [セキュリティグループ, ファイアウォール, 最小権限, security-group, firewall, least-privilege, ingress]
lib: hashicorp/aws
fn: aws_security_group
since: "5.0"
verified: 2026-09-18
status: public
---

許可する `{ port, protocol, cidr | source_security_group_id, description }` のリストから、入向き規則をそれだけ持つセキュリティグループを作る。SSH / RDP の全世界公開は拒否する。

## Signature

```hcl
variables: name, description, vpc_id, ingress_rules = [{ port, protocol = "tcp", cidr | source_security_group_id, description }], allow_all_egress = true, tags = {}
outputs:   security_group_id, security_group_arn, security_group_name
```

## Usage

```hcl
module "web_sg" {
  source      = "./modules/network-security-group-minimal"
  name        = "app-web"
  description = "app の HTTPS と DB 接続だけを許可"
  vpc_id      = "vpc-0123456789abcdef0"
  ingress_rules = [
    { port = 443, cidr = "10.0.0.0/16", description = "VPC 内からの HTTPS" },
    { port = 5432, source_security_group_id = "sg-0123456789abcdef0", description = "アプリ SG からの PostgreSQL" },
  ]
}
```

## Contract

- 入向き規則は `ingress_rules` に書いたものだけ。`aws_vpc_security_group_ingress_rule` を規則ごとに 1 つ作り、`from_port = to_port = port`
- `0.0.0.0/0` / `::/0` からの 22（SSH）と 3389（RDP）は validation で拒否
- 各規則は `cidr` と `source_security_group_id` のどちらか一方だけ。両方・どちらも無しは拒否。`cidr` は IPv4 なら `cidr_ipv4`、IPv6 なら `cidr_ipv6` に入る
- 各規則と SG 本体の `description` は必須（空白のみは拒否）
- 外向きは `allow_all_egress = true`（既定）で IPv4 / IPv6 の全許可規則を 1 つずつ作る。`false` なら外向き規則を作らず、全ての外向き通信を拒否する
- 規則はインラインで書かず、すべて `aws_vpc_security_group_*_rule` リソース
- `tags` を SG と全規則に付け、SG の `Name` に `name` を入れる

## Alternatives

- 複数のポートレンジや ICMP が要るなら `aws_vpc_security_group_ingress_rule` を直接書く（この module は単一ポート・tcp / udp のみ）
- 送信元を IP でなく「役割」で表したいときは `source_security_group_id` を使う。IP が変わっても規則を直さなくてよい
- サブネット単位のステートレスな制御は NACL。ただし通常は SG だけで足りる

## Pitfalls

- `name`、`description`、`vpc_id` の変更は SG の再作成になる。`create_before_destroy` を付けてあるが、他リソースから参照されていると削除に失敗する
- 同じ SG に `aws_security_group` のインライン `ingress` / `egress` や `aws_security_group_rule` を混ぜると、規則が消し合って差分が出続ける
- `allow_all_egress = false` にすると DNS や AWS API への通信も止まる。必要な外向き規則は別途 `aws_vpc_security_group_egress_rule` で足す
- 規則の `for_each` キーは `<protocol>-<port>-<送信元>`。同じ組み合わせの規則を 2 つ書くと後勝ちで 1 つになる

## Test

`modules/network-security-group-minimal/tests/network-security-group-minimal.tftest.hcl`
