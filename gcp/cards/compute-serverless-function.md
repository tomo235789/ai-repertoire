---
id: compute-serverless-function
lang: gcp
title: イベント駆動のサーバーレス関数を配置する
tags: [CloudFunctions, PubSub, 再試行, イングレス, cloud-functions, pubsub-trigger, retry, ingress]
lib: gcp.functions
fn: serverless_function_config
since: "2024"
verified: 2026-09-19
status: public
---

「トピックにメッセージが来たら関数を動かす。失敗したら再試行する」という要求から Cloud Functions（第 2 世代）の定義を組み立てる。API は呼ばない。

## Signature

```python
def serverless_function_config(name: str, runtime: str, entry_point: str, source_bucket: str, source_object: str, service_account: str, *, memory: str = '256Mi', timeout_seconds: int = 60, max_instances: int = 100, event_trigger_topic: str | None = None, retry_on_failure: bool | None = None, ingress: str = 'ALLOW_INTERNAL_ONLY', env: dict[str, str] | None = None) -> dict
```

## Usage

```python
body = serverless_function_config(
    "example-fn", "python312", "handle", "example-bucket", "src.zip",
    "fn-runner@my-project.iam.gserviceaccount.com",
    event_trigger_topic="projects/my-project/topics/orders",
)
client.create_function(
    parent="projects/my-project/locations/asia-northeast1",
    function_id="example-fn", function=body,
)
```

## Contract

- `event_trigger_topic` を渡すと Pub/Sub 起動、省略すると HTTP 関数になり `event_trigger` は入らない
- `retry_on_failure` を省略するとイベント関数は再試行あり、HTTP 関数は再試行なしになる。HTTP 関数に `True` を渡すと `ValueError`
- `ingress` の既定は `"ALLOW_INTERNAL_ONLY"`、送信は `"PRIVATE_RANGES_ONLY"`
- 環境変数は名前順に並ぶ。名前が `password` / `secret` / `token` / `key` で終わると `ValueError`
- 実行に使うサービスアカウントは必須
- `ValueError`: 名前の形式違い、`RUNTIMES` に無いランタイム、入口が空、メモリの形式違い、最大インスタンス数が 1 未満、未知の ingress、タイムアウトが上限超（HTTP 関数は 3600 秒、イベント関数は 540 秒）
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/compute-serverless-function.py` — Lambda 関数
- `azure/examples/compute-serverless-function.py` — 関数アプリ
- 常駐させたいなら `compute-container-service` を使う
- 秘密を渡すなら環境変数ではなく `secret-fetch-at-runtime` の Secret Manager 参照を使う

## Pitfalls

- 再試行は同じイベントを何度も渡す。処理は冪等にする。冪等にできないなら再試行を切って配信不能トピックへ回す
- 再試行に上限時間はあるが回数の上限は無い。壊れたメッセージが延々と再試行され続けることがある
- 第 2 世代の関数は Cloud Run の上で動く。Cloud Run 側の設定やログもあわせて見る
- タイムアウトの上限はイベント関数が 540 秒、HTTP 関数が 3600 秒。長い処理は Cloud Run ジョブへ出す
- ソースはバケットに置いたアーカイブから読む。デプロイのたびにオブジェクト名を変えないと更新されないことがある
- ランタイムには廃止期限がある。`RUNTIMES` は廃止済みのものを載せない。期限切れのランタイムでは新規作成も更新もできない

## Test

`examples/compute-serverless-function_test.py`
