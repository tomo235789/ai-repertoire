---
id: queue-fifo-with-dlq
lang: azure
title: 順序保証と失敗メッセージの退避付きのキューを作る
tags: [ServiceBus, セッション, 配信不能キュー, 重複検出, service-bus, session, dead-letter, duplicate-detection]
lib: azure.servicebus
fn: fifo_queue_with_dlq
since: "2024"
verified: 2026-09-19
status: public
---

「同じ相手の処理は順番どおり、何度やっても駄目なものは別の場所へ」という要求から Service Bus キューの設定を組み立てる。API は呼ばない。

## Signature

```python
def fifo_queue_with_dlq(name: str, *, lock_seconds: int = 60, max_delivery_count: int = 5, message_ttl_seconds: int = 1209600, duplicate_detection_seconds: int = 600, max_size_megabytes: int = 1024) -> dict
```

## Usage

```python
props = fifo_queue_with_dlq("orders", lock_seconds=90)
client.queues.create_or_update("example-rg", "example-ns", "orders", props)
```

## Contract

- `requiresSession` は常に `True`。順序は同じセッション ID のメッセージのあいだでだけ保たれる
- `deadLetteringOnMessageExpiration` は常に `True`。期限切れも黙って消えず配信不能キューへ入る
- `maxDeliveryCount` を超えて失敗したメッセージは配信不能キューへ移る
- 期間はすべて ISO 8601 の duration 文字列。90 秒なら `"PT1M30S"`、1 日なら `"P1D"`
- `duplicate_detection_seconds=0` で重複検出は無効になり、窓のキー自体が入らない
- `enablePartitioning` は常に `False`
- `ValueError`: 名前の形式違い（1〜260 文字。1 文字でも有効）、ロック時間が 1〜300 秒の外、配信回数が 1 未満、最大サイズが `ALLOWED_SIZES_MEGABYTES` に無い値、重複検出の窓が 0 でも 20 秒〜7 日でもない、メッセージの寿命が重複検出の窓以下
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/queue-fifo-with-dlq.py` — SQS の FIFO キューと再ドライブポリシー
- `gcp/examples/queue-fifo-with-dlq.py` — Pub/Sub の順序指定キーとデッドレタートピック
- 1 つのイベントを複数の相手に配るなら `queue-fanout-topic` を使う
- 順序が要らないならセッションを使わない方が並列度が上がる

## Pitfalls

- 順序が保たれるのは**同じセッション ID のあいだ**だけ。キュー全体の順序ではない
- セッション必須のキューは、受信側もセッションレシーバーで受ける必要がある。通常の受信では 1 件も取れない
- ロックは最大 5 分。それより長い処理はロックを延長するか、処理をキューの外へ出す
- 配信不能キューは自動では空にならない。溜まり続けるとキューのサイズ上限に当たる
- 重複検出は MessageId が同じものだけを弾く。ID を付けずに送ると効かない

## Test

`examples/queue-fifo-with-dlq_test.py`
