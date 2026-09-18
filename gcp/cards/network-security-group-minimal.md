---
id: network-security-group-minimal
lang: gcp
title: 必要なポートだけを開けるファイアウォール規則を作る
tags: [ファイアウォール, ネットワークタグ, 優先度, IAP, firewall, network-tag, priority, iap]
lib: gcp.compute
fn: minimal_firewall_rules
since: "2024"
verified: 2026-09-19
status: public
---

「このタグの付いた VM に、この送信元からこのポートだけ。残りは落とす」という要求から VPC ファイアウォール規則を組み立てる。API は呼ばない。

## Signature

```python
def minimal_firewall_rules(network: str, target_tag: str, allowed, *, protocol: str = 'tcp') -> list[dict]
```

## Usage

```python
rules = minimal_firewall_rules(
    "example-vpc", "app", [("0.0.0.0/0", 443), ("10.0.0.0/8", 8080)]
)
for rule in rules:
    client.firewalls().insert(project="my-project", body=rule).execute()
```

## Contract

- 許可規則は優先度 1000、最後の全拒否は優先度 65000
- 同じ送信元のポートは 1 本の規則にまとまり、ポートは数値順の文字列で入る
- 規則は送信元 CIDR 順に並ぶ
- すべての規則が `targetTags` で絞られ、`logConfig.enable` が `True`
- `ValueError`: タグ名の形式違い、許可リストが空、ポートが 1〜65535 の外、送信元が CIDR でないかホスト部が残っている、プロトコルが `tcp` / `udp` 以外
- 22 / 3389 / 5985 / 5986 を `0.0.0.0/0` に開こうとすると `ValueError`
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/network-security-group-minimal.py` — セキュリティグループの ingress 規則
- `azure/examples/network-security-group-minimal.py` — NSG の受信規則
- 管理アクセスには規則を開けず Identity-Aware Proxy の TCP 転送を使う
- 階層型のポリシーで組織全体に効かせたいなら VPC ファイアウォールではなく階層型ファイアウォールポリシーを使う

## Pitfalls

- VPC の既定では受信が暗黙に拒否され、送信が暗黙に許可されている。優先度 65535 の暗黙規則より前に自分の規則を置く
- 既定のネットワークには `default-allow-ssh` のような広い規則が最初から入っている。消さないと全拒否が効かない
- ネットワークタグは誰でも VM に付けられる。タグを付ける権限が広いと規則を迂回できる。サービスアカウント単位の絞り込みの方が強い
- 優先度が同じ規則では拒否が許可に勝つ
- 規則を消してもすでに確立している接続はすぐには切れない

## Test

`examples/network-security-group-minimal_test.py`
