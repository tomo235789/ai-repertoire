---
id: network-security-group-minimal
lang: aws
title: 必要なポートだけを開けるファイアウォール規則を作る
tags: [セキュリティグループ, ファイアウォール, 最小権限, security group, firewall, ingress, egress, ec2]
lib: aws.ec2
fn: minimal_security_group
since: "2024"
verified: 2026-09-18
status: public
---

送信元（CIDR か別の SG）とポートを明示した ingress だけを持つセキュリティグループを組み立てる。出力は boto3 `ec2` の `create_security_group` / `authorize_security_group_ingress` / `authorize_security_group_egress` / `revoke_security_group_egress` の kwargs。

## Signature

```python
minimal_security_group(name: str, vpc_id: str, ingress: list[Rule], egress_all: bool = False, description: str | None = None) -> dict
```

## Usage

```python
from importlib import import_module

m = import_module("network-security-group-minimal")
cfg = m.minimal_security_group("app", "vpc-0abc", [
    m.Rule(443, "from ALB", source_sg="sg-0alb"),
    m.Rule(8080, "from office", cidr="10.0.0.0/8"),
])
# cfg["create_security_group"] -> ec2.create_security_group(**...)
# cfg["authorize_ingress"]     -> ec2.authorize_security_group_ingress(GroupId=..., IpPermissions=...)
# cfg["revoke_egress"]         -> 作成時に自動付与される全許可 egress を revoke_security_group_egress で消す
```

## Contract

- 副作用無し。同じ入力から同じ出力。`Rule` は frozen dataclass で変更されない。出力は `json.dumps` できる
- `Rule` は `description` 必須（空白のみも不可）、`cidr` と `source_sg` はどちらか一方だけ。両方・どちらも無しは `ValueError`
- `0.0.0.0/0` または `::/0` から 22 / 3389 を含むポート範囲を開ける規則は `ValueError`。送信元が限定された CIDR なら 22 も通る
- `protocol` は `tcp` / `udp` のみ。`-1`（全プロトコル）は `ValueError`。ポートは 0〜65535、`to_port` は `port` 以上
- IPv4 CIDR は `IpRanges`、IPv6 CIDR は `Ipv6Ranges`、`source_sg` は `UserIdGroupPairs` に入り、いずれも `Description` を持つ
- 既定は egress 無し: `authorize_egress` は空、`revoke_egress` に作成時の既定 egress（`-1` / `0.0.0.0/0`）を返す。`egress_all=True` で逆になる
- `create_security_group.Description` は `description` 省略時に `name`

## Alternatives

- Terraform: `terraform/modules/network-security-group-minimal`（同じ ID。`aws_security_group` + `aws_vpc_security_group_ingress_rule`）
- CloudFormation: `AWS::EC2::SecurityGroup`（`SecurityGroupEgress` を空にすると既定の全許可を自動で消す）
- 22 / 3389 の代わりに SSM Session Manager（インバウンド不要）。RDS など他の SG からだけ受けるなら `source_sg`

## Pitfalls

- `create_security_group` は egress 全許可を自動で付ける。`egress_all=False` の意図を守るには `revoke_egress` を必ず呼ぶ。忘れると「最小」にならない
- `authorize_ingress` / `revoke_egress` の kwargs に `GroupId` は無い。`create_security_group` の応答 `GroupId` を足して渡す
- `GroupName` と `VpcId` は作成後に変更できない。VPC 内で `GroupName` は一意
- IPv6 の `::/0` からの egress は `egress_all=True` でも作らない（`Ipv6Ranges` を自分で足す）
- 同じ規則を 2 回 authorize すると `InvalidPermission.Duplicate`。冪等にするなら `describe_security_group_rules` で差分を取る

## Test

`examples/network-security-group-minimal_test.py`
