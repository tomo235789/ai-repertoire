---
id: network-private-subnet
lang: gcp
title: インターネットから直接到達できないプライベートサブネットを作る
tags: [サブネット, 限定公開アクセス, 副レンジ, フローログ, subnetwork, private-google-access, secondary-range, flow-logs]
lib: gcp.compute
fn: private_subnet_config
since: "2024"
verified: 2026-09-19
status: public
---

「外部 IP を持たせず、Google の API へは内部経路で出す」という要求からサブネットを組み立てる。使えるアドレス数も返す。API は呼ばない。

## Signature

```python
def private_subnet_config(name: str, network: str, ip_cidr_range: str, region: str, *, secondary_ranges: dict[str, str] | None = None, flow_log_sampling: float = 0.5, purpose: str = 'PRIVATE') -> dict
```

## Usage

```python
cfg = private_subnet_config(
    "app", "example-vpc", "10.0.1.0/24", "asia-northeast1",
    secondary_ranges={"pods": "10.1.0.0/16", "services": "10.2.0.0/20"},
)
client.subnetworks().insert(
    project="my-project", region="asia-northeast1", body=cfg["subnetwork"]
).execute()
```

## Contract

- `privateIpGoogleAccess` は常に `True`
- フローログは常に有効。集計間隔は 5 秒、メタデータは全件、サンプリング率は引数で決まる
- 副レンジは名前順に並ぶ。1 件も無ければ `secondaryIpRanges` のキー自体を作らない
- `usable_addresses` はアドレス総数から GCP の予約 4 個を引いた数
- `ValueError`: 名前や副レンジ名の形式違い、CIDR が不正、ホスト部が残っている、プレフィックスが /29 より小さい、副レンジが主レンジや他の副レンジと重なる、サンプリング率が 0 以下か 1.0 超
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/network-private-subnet.py` — プライベートサブネットと NAT ゲートウェイ
- `azure/examples/network-private-subnet.py` — サブネットと NAT ゲートウェイ
- マネージドサービスへの接続だけなら `network-private-endpoint` の Private Service Connect を使う
- 外部への通信が要るなら Cloud NAT を別に作る。サブネット側の設定ではない

## Pitfalls

- GCP は各サブネットで 4 アドレスを予約する。/29 なら使えるのは 4 つだけ
- 限定公開の Google アクセスは Google の API に出られるようにするだけ。インターネット全体には出られない
- 副レンジは GKE の Pod と Service に使う。作成後に広げられないので最初に多めに取る
- 主レンジは拡張できるが縮められない。副レンジは変更できない
- フローログは全件取ると費用がかさむ。サンプリング率で調整する

## Test

`examples/network-private-subnet_test.py`
