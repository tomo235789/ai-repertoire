---
id: network-security-group-minimal
lang: azure
title: 必要なポートだけを開けるファイアウォール規則を作る
tags: [NSG, 受信規則, 優先度, 最小開放, nsg, security-rules, priority, deny-all]
lib: azure.network
fn: minimal_inbound_rules
since: "2024"
verified: 2026-09-19
status: public
---

「この送信元からこのポートだけ。残りは全部落とす」という要求から NSG の受信規則を組み立てる。API は呼ばない。

## Signature

```python
def minimal_inbound_rules(allowed, *, protocol: str = 'Tcp') -> list[dict]
```

## Usage

```python
rules = minimal_inbound_rules([("Internet", 443), ("10.0.0.0/8", 8080)])
client.network_security_groups.begin_create_or_update(
    "example-rg", "example-nsg", {"location": "japaneast", "security_rules": rules}
).result()
```

## Contract

- 規則は優先度 100 から 10 刻みで並び、最後に優先度 4000 の全拒否が必ず入る
- 規則名は `allow-<連番>-port-<ポート>`。送信元をそのまま入れると IPv6 のコロンが名前に混ざるため使わない
- 同じ (送信元, ポート) を 2 度渡しても規則は 1 本にまとまる。並びは送信元・ポート順で決まる
- 送信元は CIDR かサービスタグ。英字で始まる値はサービスタグとしてそのまま通す
- `ValueError`: 許可リストが空、ポートが 1〜65535 の外、CIDR の形式違いかホスト部が残っている、プロトコルが `Tcp` / `Udp` / `*` 以外、規則が多すぎて全拒否の優先度に届く場合
- 22 / 3389 / 5985 / 5986 をインターネット（`*`、`Internet`、`0.0.0.0/0`、`::/0`）から開こうとすると `ValueError`。CIDR はプレフィックス長 0 を IPv4 と IPv6 の両方で見る
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/network-security-group-minimal.py` — セキュリティグループの ingress 規則
- `gcp/examples/network-security-group-minimal.py` — VPC ファイアウォール規則
- 管理アクセスが要るなら規則を開けず Azure Bastion か Just-In-Time アクセスを使う
- 送信方向も絞るなら同じ形で `direction: "Outbound"` の規則を別に作る

## Pitfalls

- NSG の既定規則は仮想ネットワーク内の通信と Azure ロードバランサーを許している。優先度 4000 の全拒否はそれより前に評価されるので、必要な内部通信は明示的に許可する
- 優先度は 100〜4096。番号が若いほど先に評価され、最初に一致した規則で決まる
- サブネットと NIC の両方に NSG を付けると、受信は両方を通過しないと届かない。片方だけ直しても効かないことがある
- 送信元に `*` を書くとインターネットだけでなく仮想ネットワーク内も含む。内部だけなら `VirtualNetwork` タグを使う
- 規則を消してもすでに確立している接続はすぐには切れない

## Test

`examples/network-security-group-minimal_test.py`
