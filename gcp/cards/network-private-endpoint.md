---
id: network-private-endpoint
lang: gcp
title: インターネットを経由せずにマネージドサービスへ接続する
tags: [PrivateServiceConnect, サービスアタッチメント, 転送ルール, DNS, private-service-connect, service-attachment, forwarding-rule, dns]
lib: gcp.compute
fn: private_endpoint_config
since: "2024"
verified: 2026-09-19
status: public
---

「公開 IP を通さずに Google API や他プロジェクトのサービスへ繋ぐ」という要求から Private Service Connect の転送ルールと DNS を組み立てる。API は呼ばない。

## Signature

```python
def private_endpoint_config(name: str, network: str, ip_address: str, *, target_service: str | None = None, api_bundle: str | None = None, subnetwork: str | None = None, allow_psc_global_access: bool = False) -> dict
```

## Usage

```python
cfg = private_endpoint_config(
    "pscapis", "example-vpc", "10.0.0.100", api_bundle="all-apis"
)
client.globalForwardingRules().insert(
    project="my-project", body=cfg["forwarding_rule"]
).execute()
```

## Contract

- `api_bundle` を渡すと `scope` は `"global"` になり、`dns_zone` に `p.googleapis.com` のプライベートゾーンが返る
- `target_service` を渡すと `scope` は `"regional"` になり、`subnetwork` が必須。`dns_zone` は `None`
- `allow_psc_global_access` は既定で `False`。他リージョンからの接続は明示したときだけ
- `target_service` と `api_bundle` はどちらか一方だけ。両方でも両方省略でも `ValueError`
- `PRIVATE_GOOGLE_ACCESS_VIP_RANGES` は限定公開の Google アクセスで使う VIP レンジ。Private Service Connect のエンドポイントには自分で予約した内部 IP を渡す
- `ValueError`: 名前の形式違い、IP アドレスが不正、API バンドル向けに IPv6 を指定、未知のバンドル、個別サービスにサブネットが無い
- バンドル向けの転送ルール名は英小文字と数字だけで 20 文字まで。ハイフンは使えない
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/network-private-endpoint.py` — VPC エンドポイント
- `azure/examples/network-private-endpoint.py` — プライベートエンドポイントと DNS ゾーングループ
- Google API へ出るだけなら限定公開の Google アクセス（`network-private-subnet`）で足りることが多い
- 自分のサービスを他プロジェクトへ公開するならサービスアタッチメントを作る側になる

## Pitfalls

- 転送ルールを作っても DNS が公開 IP を返すままだと閉域にならない。`p.googleapis.com` のプライベートゾーンを VPC に紐付ける
- Google API 向けのバンドルは `all-apis` と `vpc-sc` で対象が違う。VPC Service Controls を使うなら後者
- 個別サービスへのエンドポイントは同じリージョンからしか繋がらない。他リージョンからは `allowPscGlobalAccess` が要る
- サービスアタッチメント側が接続を承認するまで通信は通らない
- エンドポイントの IP はサブネットから消費される。サブネットのレンジを使い切らないようにする

## Test

`examples/network-private-endpoint_test.py`
