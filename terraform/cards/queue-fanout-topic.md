---
id: queue-fanout-topic
lang: terraform
title: 1 つのイベントを複数の購読者に配信する
tags: [ファンアウト, トピック, 購読, イベント配信, sns, sqs, fanout, pub-sub]
lib: hashicorp/aws
fn: aws_sns_topic
since: "5.0"
verified: 2026-09-18
status: public
---

1 つの SNS トピックから複数の SQS キューへメッセージを複製配信する。各キューは「このトピックからの送信」だけを受け付ける。

## Signature

```hcl
variables: topic_name, queue_names, raw_message_delivery? = false, visibility_timeout_seconds? = 30,
           message_retention_seconds? = 345600, kms_key_id?, tags?
outputs:   topic_id, topic_arn, topic_name, queue_ids, queue_arns, subscription_arns  # queue_* はキュー名 → 値の map
```

## Usage

```hcl
module "order_events" {
  source               = "./modules/queue-fanout-topic"
  topic_name           = "example-order-events"
  queue_names          = ["example-billing", "example-notify"]
  raw_message_delivery = true
  tags                 = { env = "example" }
}
# 発行側: sns:Publish を module.order_events.topic_arn に限定して許可する
```

## Contract

- `queue_names` の各要素につき、SQS キュー・キューポリシー・SNS サブスクリプションを 1 つずつ作る（`for_each`、キューは名前でキーされる）
- 各キューポリシーは Statement 1 つで、`Principal = sns.amazonaws.com`、`Action = sqs:SendMessage` のみ、`Resource` はそのキューの ARN、`Condition ArnEquals aws:SourceArn` がこのトピックの ARN。他のトピックや任意の principal からは送れない
- サブスクリプションは `protocol = sqs`。`raw_message_delivery` は既定 `false`（SNS の通知 JSON、本文は `Message` フィールド）で変数で切り替えられる
- 保存時暗号化: `kms_key_id` 未指定なら各キューに `sqs_managed_sse_enabled = true`（SSE-SQS）、トピックは暗号化なし。指定すればトピックと各キューの両方に `kms_master_key_id`
- `queue_names` が空・重複あり・`.fifo` で終わる要素あり、`topic_name` が `.fifo` で終わる場合は validation で拒否する（標準トピック / 標準キューのみ）
- `tags` はトピックと各キューに付く（サブスクリプションとキューポリシーはタグを持たない）
- サブスクリプションはキューポリシーの後に作る（`depends_on`）ので、購読直後の配信がポリシー未設定で落ちない

## Alternatives

- EventBridge（`aws_cloudwatch_event_rule` + ターゲット）: イベントの内容でルーティングしたい、他 AWS サービスや SaaS のイベントも扱いたいとき。配信の遅延と料金は SNS より大きい
- 購読者ごとに受け取るメッセージを絞るなら `aws_sns_topic_subscription.filter_policy` を追加する（この module は全キューに全メッセージを配る）
- 順序保証が要るなら SNS FIFO トピック（`.fifo`）+ SQS FIFO。この module は標準のみ

## Pitfalls

- 顧客管理キーを使うとき、キーポリシーで `sns.amazonaws.com` に `kms:GenerateDataKey*` と `kms:Decrypt` を許可しないと SNS がキューへ書けず、配信が黙って失敗する
- `raw_message_delivery = false` のとき、購読側は本文をそのまま使えない。SNS の通知 JSON をパースして `Message` を取り出す
- SNS → SQS の配信失敗は既定で再試行後に破棄される。取りこぼしを見たいならサブスクリプションに `redrive_policy`（配信 DLQ）を付ける
- SNS のメッセージは最大 256 KB。大きなペイロードは S3 に置いてキーを配る

## Test

`modules/queue-fanout-topic/tests/queue-fanout-topic.tftest.hcl`
