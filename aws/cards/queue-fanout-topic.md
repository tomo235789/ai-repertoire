---
id: queue-fanout-topic
lang: aws
title: 1 つのイベントを複数の購読者に配信する
tags: [ファンアウト, SNS, SQS, ラップメッセージ, キューポリシー, RawMessageDelivery, event-bus, multi-subscriber]
lib: aws.sns
fn: fanout
since: "2024"
verified: 2026-09-18
status: public
---

「1 つのイベントを複数の SQS キューに並列配信するファンアウト構成」という要求から、SNS トピック作成 / 購読設定 / 各キューのキューポリシー の 3 種類を組み立てる。トピックはデフォルトで AWS 管理キーで暗号化する。

## Signature

```python
def fanout(topic_name: str, queue_arns: Sequence[str], region: str, account_id: str, raw_message_delivery: bool = True, kms_key_id: str | None = None, *, tags: Mapping[str, str] | None = None) -> dict[str, Any]
```

## Usage

```python
from queue_fanout_topic import fanout  # examples/queue-fanout-topic.py をコピー

out = fanout("order-events", [Q1, Q2], "us-east-1", "123456789012")
sns.create_topic(**out["create_topic"])                              # トピック作成。Attributes に KmsMasterKeyId
for sub in out["subscriptions"]:                                     # 各キューへの購読（RawMessageDelivery=true）
    sns.subscribe(**sub)
for arn, policy in out["queue_policies"].items():                    # 各キューのポリシー（このトピックからの sendMessage のみ許可）
    sqs.set_queue_attributes(QueueUrl=url, Attributes={"Policy": json.dumps(policy)})
```

## Contract

- `subscriptions` は queue_arns の数だけエントリを持つリスト。Protocol はすべて `"sqs"` 、RawMessageDelivery は文字列 `"true"` / `"false"`
- `queue_policies` はキュー ARN をキーとする辞書。各値は `sqs:SendMessage` のみ許可するポリシーで、Condition に `aws:SourceArn: <トピックARN>` が含まれる
- トピックの `KmsMasterKeyId` は既定 `alias/aws/sns`。kms_key_id を指定すればそちらを使う
- FIFO トピック（`.fifo` 終わり）なら `FifoTopic: "true"` が付く。標準トピックには付かない
- FIFO トピックに FIFO キュー以外、標準トピックに FIFO キューを購読させると ValueError
- queue_arns は 1 つ以上必要で重複禁止。SQS 形式外の ARN も ValueError
- 同じ入力に同じ出力を返し、入力を不変。全体を `json.dumps` できる

## Alternatives

- Terraform resource `terraform/modules/queue-fanout-topic`（同じ id。`aws_sns_topic` + `aws_sns_topic_subscription` + `aws_sqs_queue_policy` を同じ既定値で）
- CloudFormation `AWS::SNS::Topic` + `AWS::SNS::Subscription` + `AWS::SQS::QueuePolicy`。订阅の Attributes に RawMessageDelivery を設定

## Pitfalls

- トピック ARN はリージョンとアカウントに依存する。queue_arns と同じリージョン・アカウントで正しく組み立てる必要がある
- キューポリシーは set_queue_attributes で設定。`aws:SourceArn` でこのトピックからの送信を制限し、他のソースからの直接送信を弾く
- トピック名が `.fifo` のとき、すべての購読先キューも `.fifo` であること。FIFO と標準の混在は SNS が拒否する
- `raw_message_delivery=False` の場合、SQS に届くメッセージには envelope（topic ARN, messageId など）が含まれる。ハンドラがこれを考慮する

## Test

`examples/queue-fanout-topic_test.py`
