---
id: queue-fifo-with-dlq
lang: gcp
title: 順序保証と失敗メッセージの退避付きのキューを作る
tags: [PubSub, 順序指定キー, デッドレター, 一度だけ, pubsub, message-ordering, dead-letter, exactly-once]
lib: gcp.pubsub
fn: ordered_subscription_with_dlq
since: "2024"
verified: 2026-09-19
status: public
---

「同じキーのメッセージは順番どおり、何度やっても駄目なものは別トピックへ」という要求から Pub/Sub の購読設定を組み立てる。API は呼ばない。

## Signature

```python
def ordered_subscription_with_dlq(topic: str, subscription: str, dead_letter_topic: str, *, ack_deadline_seconds: int = 60, max_delivery_attempts: int = 5, message_retention_days: int = 7, enable_exactly_once: bool = True, filter_expression: str | None = None) -> dict
```

## Usage

```python
cfg = ordered_subscription_with_dlq(
    "projects/my-project/topics/orders",
    "projects/my-project/subscriptions/orders-worker",
    "projects/my-project/topics/orders-dead-letter",
)
client.create_subscription(request=cfg["subscription_config"])
```

## Contract

- `enable_message_ordering` と `enable_exactly_once_delivery` は既定で `True`
- `dead_letter_policy` で試行回数を超えたメッセージを配信不能トピックへ送る
- 再試行は最小 10 秒・最大 600 秒の指数バックオフ
- 期間はすべて秒で渡す。7 日なら `{"seconds": 604800}`
- `filter` は渡したときだけ入る
- `ValueError`: 名前が `projects/<project>/topics/<id>` か `projects/<project>/subscriptions/<id>` の形でない（種別の取り違えも弾く）、名前の形式違い、配信不能トピックが購読元と同じ、確認応答の期限が 10〜600 秒の外、試行回数が 5〜100 の外、保持日数が 1〜7 の外
- 同じ入力に同じ出力を返し、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/queue-fifo-with-dlq.py` — SQS の FIFO キューと再ドライブポリシー
- `azure/examples/queue-fifo-with-dlq.py` — Service Bus のセッションと配信不能キュー
- 1 つのイベントを複数の相手へ配るなら `queue-fanout-topic` を使う
- 順序が要らないなら順序指定を切った方がスループットが出る

## Pitfalls

- 順序が保たれるのは**同じ順序指定キーのあいだ**だけ。送る側がキーを付けないと効かない
- 順序指定を有効にすると、失敗したメッセージが確認されるまで同じキーの後続が止まる。詰まりに気付けるよう監視する
- 配信不能トピックへ送るには、Pub/Sub のサービスアカウントに発行とサブスクライブの権限が要る。無いと退避されず再試行が続く
- 一度だけの配信は購読側の確認応答が期限内に返ることが前提。重い処理では期限を延長する
- 配信不能トピックにも購読を作っておかないと、退避したメッセージが保持期間で消える

## Test

`examples/queue-fifo-with-dlq_test.py`
