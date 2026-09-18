"""カード queue-fifo-with-dlq: FIFO キューと、その失敗メッセージを退避するデッドレターキュー（DLQ）

sqs.create_queue の kwargs を DLQ 用とメインキュー用の 2 つ返す。DLQ を先に作る。
RedrivePolicy は SQS の仕様どおり JSON 文字列にしてある。
"""

from __future__ import annotations

import json
import re
from typing import Any, Mapping

_QUEUE_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,75}\.fifo$")
_REGION_RE = re.compile(r"^[a-z]{2}(?:-[a-z]+)+-\d$")
_ACCOUNT_RE = re.compile(r"^\d{12}$")

DLQ_SUFFIX = "-dlq"
DLQ_RETENTION_SECONDS = 14 * 24 * 60 * 60  # SQS の最大値。失敗メッセージを最長で保持する
MAX_RECEIVE_COUNT_RANGE = (1, 1000)
VISIBILITY_TIMEOUT_RANGE = (0, 43200)


def dlq_name_for(name: str) -> str:
    """メインキュー名から DLQ 名を作る（`orders.fifo` → `orders-dlq.fifo`）"""
    return name.removesuffix(".fifo") + DLQ_SUFFIX + ".fifo"


def fifo_queue_with_dlq(
    name: str,
    region: str,
    account_id: str,
    max_receive_count: int = 5,
    visibility_timeout: int = 30,
    kms_key_id: str | None = None,
    *,
    content_based_deduplication: bool = False,
    tags: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """FIFO キューと DLQ の create_queue kwargs を返す。

    :param name: `.fifo` で終わるキュー名（80 文字以内）
    :param region: DLQ の ARN を組み立てるためのリージョン（RedrivePolicy に必要）
    :param account_id: 同上。12 桁
    :param max_receive_count: この回数受信しても削除されなければ DLQ へ移す（1〜1000）
    :param visibility_timeout: 可視性タイムアウト秒（0〜43200）
    :param kms_key_id: CMK で暗号化するならその ID / ARN / エイリアス。None なら SQS 管理の SSE
    :returns: {"dlq": create_queue kwargs, "queue": create_queue kwargs}
    """
    if not _QUEUE_NAME_RE.match(name):
        raise ValueError(f"FIFO キュー名は英数字・-・_ で 80 文字以内、末尾が .fifo: {name!r}")
    if not _REGION_RE.match(region):
        raise ValueError(f"リージョン名が不正: {region!r}")
    if not _ACCOUNT_RE.match(account_id):
        raise ValueError(f"account_id は 12 桁の数字: {account_id!r}")
    lo, hi = MAX_RECEIVE_COUNT_RANGE
    if isinstance(max_receive_count, bool) or not isinstance(max_receive_count, int) or not lo <= max_receive_count <= hi:
        raise ValueError(f"max_receive_count は {lo}〜{hi} の int（実際: {max_receive_count!r}）")
    lo, hi = VISIBILITY_TIMEOUT_RANGE
    if isinstance(visibility_timeout, bool) or not isinstance(visibility_timeout, int) or not lo <= visibility_timeout <= hi:
        raise ValueError(f"visibility_timeout は {lo}〜{hi} の int（実際: {visibility_timeout!r}）")

    dlq_name = dlq_name_for(name)
    dlq_arn = f"arn:aws:sqs:{region}:{account_id}:{dlq_name}"
    sse: dict[str, str] = {"KmsMasterKeyId": kms_key_id} if kms_key_id else {"SqsManagedSseEnabled": "true"}

    dlq_attributes: dict[str, str] = {
        "FifoQueue": "true",
        "MessageRetentionPeriod": str(DLQ_RETENTION_SECONDS),
        **sse,
    }
    queue_attributes: dict[str, str] = {
        "FifoQueue": "true",
        "VisibilityTimeout": str(visibility_timeout),
        "RedrivePolicy": json.dumps({"deadLetterTargetArn": dlq_arn, "maxReceiveCount": max_receive_count}),
        **sse,
    }
    if content_based_deduplication:
        queue_attributes["ContentBasedDeduplication"] = "true"

    dlq: dict[str, Any] = {"QueueName": dlq_name, "Attributes": dlq_attributes}
    queue: dict[str, Any] = {"QueueName": name, "Attributes": queue_attributes}
    if tags:
        dlq["tags"] = dict(sorted(tags.items()))
        queue["tags"] = dict(sorted(tags.items()))
    return {"dlq": dlq, "queue": queue}
