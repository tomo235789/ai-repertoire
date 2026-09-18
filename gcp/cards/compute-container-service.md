---
id: compute-container-service
lang: gcp
title: コンテナを常駐サービスとして実行する
tags: [CloudRun, スケーリング, 同時実行数, イングレス, cloud-run, scaling, concurrency, ingress]
lib: gcp.run
fn: container_service_config
since: "2024"
verified: 2026-09-19
status: public
---

「このイメージをサービスとして動かし、外からは直接叩かせない」という要求から Cloud Run のサービス定義を組み立てる。API は呼ばない。

## Signature

```python
def container_service_config(name: str, image: str, service_account: str, *, cpu: str = '1', memory: str = '512Mi', min_instances: int = 0, max_instances: int = 100, concurrency: int = 80, ingress: str = 'INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER', allow_unauthenticated: bool = False, env: dict[str, str] | None = None, vpc_connector: str | None = None) -> dict
```

## Usage

```python
cfg = container_service_config(
    "example-api",
    "asia-northeast1-docker.pkg.dev/my-project/app/api:1.4.2",
    "app-runner@my-project.iam.gserviceaccount.com",
)
client.create_service(
    parent="projects/my-project/locations/asia-northeast1",
    service_id="example-api", service=cfg["service"],
)
```

## Contract

- `ingress` の既定は `"INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"`。インターネットから直接は届かない
- `iam_policy` の既定は空。`allow_unauthenticated=True` のときだけ `allUsers` に `roles/run.invoker` が入る
- `service_account` は必ず入る。既定のコンピュートサービスアカウントを使わせない
- 環境変数は名前順に並ぶ。名前が `password` / `secret` / `token` / `key` で終わると `ValueError`
- `vpc_access` は `vpc_connector` を渡したときだけ入り、送信は `PRIVATE_RANGES_ONLY`
- イメージはタグかダイジェストが必須で、`latest` は `ValueError`
- `ValueError`: 名前の形式違い、サービスアカウントがメールアドレスでない、CPU やメモリの形式違い、`min_instances > max_instances`、同時実行数が 1〜1000 の外、未知の ingress
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/compute-container-service.py` — ECS サービスとタスク定義
- `azure/examples/compute-container-service.py` — Container Apps
- イベント 1 件ごとの処理なら `compute-serverless-function` の方が構成が少ない
- ノードやサイドカーの制御が要るなら Cloud Run ではなく GKE

## Pitfalls

- 同時実行数を上げるとインスタンス数は減るが、1 つのプロセスが並行して処理する。スレッドセーフでないコードは壊れる
- `min_instances=0` にするとアイドル時は無課金だが、最初の要求にコールドスタートが乗る
- `allow_unauthenticated=True` は認証を外すだけで、到達経路は ingress で決まる。`INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER` のままなら直接インターネットからは届かないが、ingress を `ALL` にした時点で無認証の公開になる
- VPC コネクタ経由の送信を `ALL_TRAFFIC` にすると、外部 API への通信も VPC を通る。Cloud NAT が無いと出られなくなる
- リビジョンは不変。環境変数を変えるたびに新しいリビジョンが作られ、トラフィックの割り当ては別に管理する

## Test

`examples/compute-container-service_test.py`
