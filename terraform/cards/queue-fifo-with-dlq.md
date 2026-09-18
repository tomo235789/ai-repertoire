---
id: queue-fifo-with-dlq
lang: terraform
title: 順序保証と失敗メッセージの退避付きのキューを作る
tags: [キュー, 順序保証, デッドレターキュー, 再試行, sqs, fifo, dlq, dead-letter]
lib: hashicorp/aws
fn: aws_sqs_queue
since: "5.0"
verified: 2026-09-18
status: public
---

FIFO の SQS キューと、規定回数処理に失敗したメッセージを退避する DLQ の組を作る。両方とも保存時暗号化を必ず有効にする。

## Signature

```hcl
variables: name, dlq_name?, max_receive_count? = 5, visibility_timeout_seconds? = 30, message_retention_seconds? = 345600,
           dlq_message_retention_seconds? = 1209600, content_based_deduplication? = false, high_throughput? = false, kms_key_id?, tags?
outputs:   queue_id, queue_arn, queue_name, dlq_id, dlq_arn, dlq_name
```

## Usage

```hcl
module "orders_queue" {
  source                     = "./modules/queue-fifo-with-dlq"
  name                       = "example-orders.fifo"
  max_receive_count          = 3
  visibility_timeout_seconds = 60
  tags                       = { env = "example" }
}
# module.orders_queue.queue_id が SDK に渡す QueueUrl
```

## Contract

- メインキューと DLQ の両方が `fifo_queue = true`。`name` / `dlq_name` が `.fifo` で終わらない値は validation で拒否する
- `dlq_name` 未指定時は `<name の .fifo の前>-dlq.fifo`
- 保存時暗号化を必ず有効にする。`kms_key_id` 未指定なら両キューに `sqs_managed_sse_enabled = true`（SSE-SQS）、指定すれば両キューに `kms_master_key_id` とデータキー再利用期間（既定 300 秒）
- `redrive_policy` は `deadLetterTargetArn` が DLQ の ARN、`maxReceiveCount` が変数（既定 5、1〜1000 のみ）
- DLQ 側の `redrive_allow_policy` は `byQueue` でメインキューの ARN だけを許可する（他キューから DLQ として使えない）
- 既定は `content_based_deduplication = false`（送信側が `MessageDeduplicationId` を付ける）、重複排除とスループット制限はキュー単位。`high_throughput = true` で `messageGroup` / `perMessageGroupId` に切り替わる
- 既定の可視性タイムアウトは 30 秒、メッセージ保持はメイン 4 日・DLQ 14 日。DLQ の保持がメインより短い組み合わせは precondition で拒否する
- `tags` は両キューに付く
- 出力の `queue_id` / `dlq_id` はキュー URL

## Alternatives

- 順序が不要なら標準キュー（`fifo_queue = false`）の方がスループット上限が無く安い。DLQ と redrive の構造は同じ
- Lambda / ECS などのイベントソースで再試行回数を制御する場合も、最終的な退避先として DLQ は残す
- 順序と大量配信の両方が必要なら SNS FIFO トピック → SQS FIFO のファンアウト

## Pitfalls

- `content_based_deduplication = true` にすると、5 分以内の同一本文は別メッセージでも捨てられる。本文が同じで意味が違うメッセージがあるなら ID を明示する
- 可視性タイムアウトは処理時間の上限より長くする。短いと処理中に再配信され、`max_receive_count` に達して DLQ へ落ちる
- DLQ 内のメッセージの残り保持時間は「元のキューに送信された時刻」から数える。DLQ の保持期間はメインより長くする（precondition で強制）
- FIFO は同じ `MessageGroupId` 内で 1 メッセージが失敗し続けると後続が詰まる。DLQ へ落として詰まりを解消するために `max_receive_count` を大きくしすぎない
- 顧客管理キーを使うとき、送信側・受信側の principal に加えて、SNS や EventBridge など「キューへ送るサービス」にもキーの `kms:GenerateDataKey*` / `kms:Decrypt` が要る

## Test

`modules/queue-fifo-with-dlq/tests/queue-fifo-with-dlq.tftest.hcl`
