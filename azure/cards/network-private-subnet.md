---
id: network-private-subnet
lang: azure
title: インターネットから直接到達できないプライベートサブネットを作る
tags: [サブネット, 仮想ネットワーク, NATゲートウェイ, 委任, subnet, vnet, nat-gateway, delegation]
lib: azure.network
fn: private_subnet_config
since: "2024"
verified: 2026-09-19
status: public
---

「外からは届かない、出るときは明示した経路だけ」という要求からサブネットの構成を組み立てる。使えるアドレス数も合わせて返す。API は呼ばない。

## Signature

```python
def private_subnet_config(name: str, address_prefix: str, *, route_table_id: str | None = None, nat_gateway_id: str | None = None, network_security_group_id: str | None = None, service_endpoints=(), delegation_service: str | None = None) -> dict
```

## Usage

```python
cfg = private_subnet_config(
    "app", "10.0.1.0/24", nat_gateway_id=nat_id, network_security_group_id=nsg_id
)
client.subnets.begin_create_or_update(
    "example-rg", "example-vnet", cfg["name"], cfg["properties"]
).result()
print(cfg["usable_addresses"])  # 251
```

## Contract

- `defaultOutboundAccess` は常に `False`。既定の送信インターネットアクセスに頼らず、NAT ゲートウェイを明示したときだけ外へ出られる
- `privateEndpointNetworkPolicies` と `privateLinkServiceNetworkPolicies` は `"Enabled"` のまま。プライベートエンドポイントにも NSG とルートを効かせる
- `usable_addresses` はアドレス総数から Azure の予約 5 個を引いた数
- `serviceEndpoints` はサービス名順に並ぶ。引数の順序が違っても同じ構成になる
- ルートテーブル・NAT・NSG・委任は渡したときだけキーが入る
- `ValueError`: 名前の形式違い、CIDR が不正、ホスト部が残っている、プレフィックスが /29 より小さい、IPv6
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/network-private-subnet.py` — プライベートサブネットと NAT ゲートウェイ
- `gcp/examples/network-private-subnet.py` — 限定公開の Google アクセスとサブネット
- マネージドサービスへの接続だけが要るならサブネットを開けず `network-private-endpoint` を使う
- 送信も一切要らないなら NAT ゲートウェイを付けず、ルートテーブルで既定経路を落とす

## Pitfalls

- Azure は各サブネットで先頭 4 つと末尾 1 つ、合わせて 5 アドレスを予約する。/29 なら使えるのは 3 つだけ
- サブネットは作成後にアドレス範囲を広げにくい。仮想ネットワークのアドレス空間から最初に多めに取る
- `defaultOutboundAccess=False` は暗黙の送信経路を止めるだけ。NAT も公開 IP もロードバランサの送信規則も無いリソースは外へ出られず、パッケージ取得やイメージ取得が止まる
- プライベートエンドポイント用のネットワークポリシーを無効にすると NSG が効かなくなる。既定で無効にしている例が多いので注意
- 委任したサブネットは、そのサービス専用になる。別の種類のリソースを置けない

## Test

`examples/network-private-subnet_test.py`
