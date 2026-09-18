---
id: queue-fanout-topic
lang: azure
title: 1 つのイベントを複数の購読者に配信する
tags: [ServiceBus, トピック, サブスクリプション, フィルタ, service-bus, topic, subscription, sql-filter]
lib: azure.servicebus
fn: fanout_topic
since: "2024"
verified: 2026-09-19
status: public
---

「1 件のイベントを、条件に合う購読者それぞれに配る」という要求から Service Bus のトピックとサブスクリプションとフィルタを組み立てる。API は呼ばない。

## Signature

```python
def fanout_topic(topic_name: str, subscribers: dict[str, str | None], *, message_ttl_days: int = 14, max_delivery_count: int = 5, duplicate_detection_days: int = 1) -> dict
```

## Usage

```python
cfg = fanout_topic("orders", {"billing": "eventType = 'OrderPlaced'", "audit": None})
client.topics.create_or_update("example-rg", "example-ns", "orders", cfg["topic"])
for sub_name, sub in cfg["subscriptions"].items():
    client.subscriptions.create_or_update(
        "example-rg", "example-ns", "orders", sub_name, sub["properties"]
    )
    if sub["rule"] is not None:
        client.rules.delete("example-rg", "example-ns", "orders", sub_name, "$Default")
```

## Contract

- トピックは `enable_partitioning: True`、`support_ordering: False`。配信量を優先する
- サブスクリプションは名前順に並ぶ。引数の順序が違っても同じ構成になる
- 各サブスクリプションで `deadLetteringOnMessageExpiration` と `deadLetteringOnFilterEvaluationExceptions` が `True`。捨てられたことに気付ける
- フィルタ式を `None` にした購読者はルールを持たず、全件を受け取る
- フィルタ式を渡した購読者には `default_rule_to_delete` に `"$Default"` が入る。既定の全通過ルールを先に消さないと絞り込みが効かない
- `duplicate_detection_days=0` で重複検出は無効になり、窓のキー自体が入らない
- `ValueError`: トピック名の形式違い、サブスクリプション名が英数字・ピリオド・ハイフン・アンダースコアの 1〜50 文字でない、購読者が空、寿命が 1 日未満、配信回数が 1 未満、重複検出の窓が 0〜7 日の外か寿命以上、フィルタ式に `;` が含まれる
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/queue-fanout-topic.py` — SNS トピックと SQS サブスクリプション
- `gcp/examples/queue-fanout-topic.py` — Pub/Sub のトピックとサブスクリプション
- 相手が 1 つで順序が要るなら `queue-fifo-with-dlq` を使う
- 購読者が Azure のサービスだけなら Event Grid の方が配信の再試行と課金の粒度が細かい

## Pitfalls

- パーティション分割を有効にしたトピックは順序を保証しない。順序が要るならサブスクリプション側でセッションを使い、分割を切る
- フィルタは既定で全件通過のルールが 1 本入る。フィルタを足しただけでは絞られないので、既定ルールを消すか置き換える
- SQL フィルタが参照できるのはシステムプロパティとアプリケーションプロパティだけ。本文の中身では絞れない
- サブスクリプションごとに配信不能キューが別にある。監視は購読者の数だけ要る
- 購読者を後から足しても、追加前に送られたメッセージは届かない

## Test

`examples/queue-fanout-topic_test.py`
