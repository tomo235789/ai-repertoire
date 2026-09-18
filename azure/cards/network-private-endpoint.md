---
id: network-private-endpoint
lang: azure
title: インターネットを経由せずにマネージドサービスへ接続する
tags: [プライベートエンドポイント, プライベートリンク, DNS, 閉域, private-endpoint, private-link, private-dns, subresource]
lib: azure.network
fn: private_endpoint_config
since: "2024"
verified: 2026-09-19
status: public
---

「この仮想ネットワークからだけ、公開エンドポイントを通さずに繋ぐ」という要求からプライベートエンドポイントと DNS ゾーングループの設定を組み立てる。API は呼ばない。

## Signature

```python
def private_endpoint_config(name: str, subnet_id: str, target_resource_id: str, group_id: str, *, manual_approval: bool = False, request_message: str = '', private_dns_zone_id: str | None = None) -> dict
```

## Usage

```python
cfg = private_endpoint_config("pe-blob", subnet_id, account_id, "blob",
                              private_dns_zone_id=zone_id)
client.private_endpoints.begin_create_or_update(
    "example-rg", "pe-blob", {"location": "japaneast", **cfg["endpoint"]}
).result()
client.private_dns_zone_groups.begin_create_or_update(
    "example-rg", "pe-blob", "default", cfg["dns_zone_group"]
).result()
```

## Contract

- 自動承認では `privateLinkServiceConnections`、`manual_approval=True` では `manualPrivateLinkServiceConnections` に入る。両方が同時に入ることはない
- `request_message` は手動承認のときだけ指定できる。自動承認で渡すと `ValueError`
- `private_dns_zone` はサブリソースに対応する `privatelink.*` のゾーン名。`PRIVATE_DNS_ZONES` に載っているキーだけ受け付ける
- `dns_zone_group` は `private_dns_zone_id` を渡したときだけ作られる。省略すると `None`
- NIC 名はエンドポイント名に `-nic` を付けたもの
- `ValueError`: 名前が空、サブネットか接続先が ARM リソース ID の形をしていない、未知のサブリソース
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/network-private-endpoint.py` — VPC エンドポイント（インターフェース型）
- `gcp/examples/network-private-endpoint.py` — Private Service Connect のエンドポイント
- 同じリージョン内で通信を Azure のバックボーンに留めるだけならサービスエンドポイントの方が安く簡単。ただし送信元は仮想ネットワークのまま公開エンドポイントを使う
- 接続先が自分のサービスならプライベートリンクサービスを作って公開する

## Pitfalls

- プライベートエンドポイントを作っても、名前解決が公開 IP のままだと通信は閉域にならない。DNS ゾーングループか条件付きフォワーダーの設定が要る
- サブリソース（`group_id`）は接続先ごとに決まっている。ストレージは `blob` と `file` で別のエンドポイントが要る
- ゾーンは仮想ネットワークにリンクして初めて効く。ゾーンを作っただけでは解決されない
- 接続先の公開ネットワークアクセスを止めないと、外からの経路は開いたまま。`storage-bucket-private` の `publicNetworkAccess` と合わせて使う
- 手動承認は接続先の所有者が承認するまで `Pending` のまま。通信は通らない

## Test

`examples/network-private-endpoint_test.py`
