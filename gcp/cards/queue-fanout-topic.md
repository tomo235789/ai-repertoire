---
id: queue-fanout-topic
lang: gcp
title: 1 つのイベントを複数の購読者に配信する
tags: [PubSub, トピック, プッシュ配信, OIDC, pubsub, topic, push-subscription, oidc]
lib: gcp.pubsub
fn: fanout_topic
since: "2024"
verified: 2026-09-19
status: public
---

「1 件のイベントを、条件に合う購読者それぞれに配る」という要求から Pub/Sub のトピックと購読を組み立てる。プッシュ配信には署名を必須にする。API は呼ばない。

## Signature

```python
def fanout_topic(topic: str, subscribers: dict[str, dict], *, subscription_project_number: str | None = None, message_retention_days: int = 1, schema: str | None = None, kms_key_name: str | None = None) -> dict
```

## Usage

```python
cfg = fanout_topic(
    "projects/my-project/topics/orders",
    {
        "projects/my-project/subscriptions/billing": {"filter": 'attributes.type = "order"'},
        "projects/my-project/subscriptions/audit": {},
    },
)
client.create_topic(request=cfg["topic_config"])
for sub in cfg["subscription_configs"]:
    client.create_subscription(request=sub)
```

## Contract

- 購読は名前順に並ぶ
- `expiration_policy` は常に空。使われない期間があっても購読が自動で消えない
- `filter` は指定した購読だけに入る
- `push_endpoint` を指定した購読は `oidc_token` 付きの `push_config` を持つ。ホスト名を持つ HTTPS 以外と、署名するサービスアカウントの無い指定は `ValueError`
- プッシュ配信を使うと `token_creator_bindings` に、Pub/Sub サービスエージェントへ `roles/iam.serviceAccountTokenCreator` を与えるバインディングが入る。無いと署名できずプッシュが失敗する。そのため ASCII 数字の `subscription_project_number` が要る
- `schema_settings` と `kms_key_name` はトピック側に、渡したときだけ入る
- `ValueError`: トピックが `projects/<project>/topics/<id>`、購読が `projects/<project>/subscriptions/<id>` の形でない、名前の形式違い、購読者が空、保持日数が 1〜31 の外、購読設定に未知のキー
- 引数を変更せず、返り値は `json.dumps` できる

## Alternatives

- `aws/examples/queue-fanout-topic.py` — SNS トピックと SQS サブスクリプション
- `azure/examples/queue-fanout-topic.py` — Service Bus のトピックとサブスクリプション
- 相手が 1 つで順序が要るなら `queue-fifo-with-dlq` を使う
- Google のサービス同士を繋ぐだけなら Eventarc の方が配線が少ない

## Pitfalls

- 購読はトピックとは別に作る。トピックだけ作ってもメッセージは誰にも届かず、保持期間で消える
- フィルタは属性にしか効かない。本文の中身では絞れない。送る側で属性を付ける
- プッシュ配信の受け側は、OIDC トークンの検証を自分で行う。検証しないと誰でも同じ URL を叩ける
- 署名に使うサービスアカウントは購読と同じプロジェクトに置く。別プロジェクトのものは `ValueError`
- 署名に使うサービスアカウントへの権限は購読を作る前に与える。後からでは最初の配信が失敗する
- 購読を後から足しても、追加前に発行されたメッセージは届かない。トピックの保持期間とシークの併用で追いつける場合はある
- `expiration_policy` を既定のままにすると、31 日使われない購読が自動的に消える

## Test

`examples/queue-fanout-topic_test.py`
