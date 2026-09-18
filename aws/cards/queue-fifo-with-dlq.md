---
id: queue-fifo-with-dlq
lang: aws
title: 順序保証と失敗メッセージの退避付きのキューを作る
tags: [FIFO, デッドレターキュー, SQS, 順序保証, RedrivePolicy, DLQ, dead-letter, retention]
lib: aws.sqs
fn: fifo_queue_with_dlq
since: "2024"
verified: 2026-09-18
status: public
---

「メッセージの順序を壊さずに受信し、失敗したメッセージを退避させる FIFO キュー」という要求から、DLQ とメインキューの `create_queue` kwargs を 2 つ組み立てる。DLQ を先に作ってから RedrivePolicy でつなぐ。

## Signature

```python
def fifo_queue_with_dlq(name: str, region: str, account_id: str, max_receive_count: int = 5, visibility_timeout: int = 30, kms_key_id: str | None = None, *, content_based_deduplication: bool = False, tags: Mapping[str, str] | None = None) -> dict[str, Any]
```

## Usage

```python
from queue_fifo_with_dlq import fifo_queue_with_dlq  # examples/queue-fifo-with-dlq.py をコピー

out = fifo_queue_with_dlq("orders.fifo", "us-east-1", "123456789012")
sqs.create_queue(**out["dlq"])                              # DLQ を先に作る（orders-dlq.fifo）
sqs.create_queue(**out["queue"])                            # メインキュー。RedrivePolicy で DLQ に繋ぐ
```

## Contract

- DLQ とメインキューの両方とも `FifoQueue: "true"`。属性値は文字列
- DLQ は `MessageRetentionPeriod: 1209600`（SQS 最大値 = 14 日）。失敗メッセージを最長で保持する
- メインキューには `RedrivePolicy` が JSON 文字列で含まれ、`deadLetterTargetArn` と `maxReceiveCount` を持つ。DLQ に RedrivePolicy は付かない
- SSE は既定 `SqsManagedSseEnabled: "true"`。`kms_key_id` を渡すと `KmsMasterKeyId` に置き換わる
- `ContentBasedDeduplication` は `True` のときだけメインキューに付く（DLQ には付かない）
- `visibility_timeout` は文字列に変換される。既定 30 秒
- 同じ入力に同じ出力を返し、入力を不変。全体を `json.dumps` できる
- `ValueError`: キュー名が `.fifo` で終わらない / 80 文字超 / 禁止文字、リージョン形式外 / アカウント ID が 12 桁以外、max_receive_count が 1〜1000 の範囲外、visibility_timeout が 0〜43200 の範囲外
- `TypeError`: max_receive_count / visibility_timeout に bool を渡すと弾く

## Alternatives

- Terraform resource `terraform/modules/queue-fifo-with-dlq`（同じ id。`aws_sqs_queue` + `aws_sqs_queue_redrive_policy` を同じ既定値で）
- CloudFormation `AWS::SQS::Queue` の `RedrivePolicy` プロパティ。FIFO キューは `FifoQueue: true`

## Pitfalls

- DLQ を先に作らないと、RedrivePolicy に含まれる ARN が存在しないキューを指すことになり `InvalidParameter` になる
- RedrivePolicy は dict ではなく JSON **文字列**。boto3 の create_queue に渡す前に json.dumps する（コード内では事前に変換済み）
- キュー名はリージョン内で一意。FIFO キューはグローバルに一意ではないが、他のアカウントと衝突の可能性はある
- SSE を有効にする場合、SqsManagedSseEnabled は文字列 `"true"` 。bool の `True` ではない

## Test

`examples/queue-fifo-with-dlq_test.py`
