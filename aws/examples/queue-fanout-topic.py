"""カード queue-fanout-topic: SNS トピックから複数の SQS キューへ配信するファンアウト構成

sns.create_topic / sns.subscribe の kwargs と、各キューに設定するキューポリシー（dict）を返す。
キューポリシーは aws:SourceArn でこのトピックからの SendMessage だけを許可する。
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

_TOPIC_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,256}$")
_FIFO_TOPIC_NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,251}\.fifo$")
_SQS_ARN_RE = re.compile(r"^arn:aws(?:-[a-z]+)?:sqs:[a-z0-9-]+:\d{12}:[A-Za-z0-9_.-]+$")
_REGION_RE = re.compile(r"^[a-z]{2}(?:-[a-z]+)+-\d$")
_ACCOUNT_RE = re.compile(r"^\d{12}$")

# CMK を渡さないときに使う AWS 管理キー。トピックを暗号化しない構成は作らない
DEFAULT_SNS_KMS_KEY = "alias/aws/sns"


def fanout(
    topic_name: str,
    queue_arns: Sequence[str],
    region: str,
    account_id: str,
    raw_message_delivery: bool = True,
    kms_key_id: str | None = None,
    *,
    tags: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """1 トピック → N キューのファンアウト設定を返す。

    :param topic_name: トピック名。`.fifo` で終わるなら FIFO トピック（購読先もすべて FIFO キューであること）
    :param queue_arns: 購読する SQS キューの ARN（1 つ以上、重複なし）
    :param region: トピック ARN を組み立てるためのリージョン
    :param account_id: 同上。12 桁
    :param raw_message_delivery: True なら SNS のエンベロープを外して本文だけをキューに入れる
    :param kms_key_id: トピックの暗号化に使う CMK。None なら AWS 管理キー alias/aws/sns
    :returns: {"create_topic": kwargs, "subscriptions": [subscribe kwargs], "queue_policies": {queue_arn: policy}}
    """
    fifo = topic_name.endswith(".fifo")
    name_re = _FIFO_TOPIC_NAME_RE if fifo else _TOPIC_NAME_RE
    if not name_re.match(topic_name):
        raise ValueError(f"トピック名が不正: {topic_name!r}（英数字・-・_ で 256 文字以内）")
    if not _REGION_RE.match(region):
        raise ValueError(f"リージョン名が不正: {region!r}")
    if not _ACCOUNT_RE.match(account_id):
        raise ValueError(f"account_id は 12 桁の数字: {account_id!r}")
    arns = list(queue_arns)
    if not arns:
        raise ValueError("queue_arns は 1 つ以上必要")
    if len(set(arns)) != len(arns):
        raise ValueError("queue_arns に重複がある")
    for arn in arns:
        if not _SQS_ARN_RE.match(arn):
            raise ValueError(f"SQS キューの ARN ではない: {arn!r}")
        if arn.endswith(".fifo") != fifo:
            raise ValueError(f"FIFO トピックには FIFO キューだけ、標準トピックには標準キューだけを購読させる: {arn!r}")

    topic_arn = f"arn:aws:sns:{region}:{account_id}:{topic_name}"
    attributes: dict[str, str] = {"KmsMasterKeyId": kms_key_id or DEFAULT_SNS_KMS_KEY}
    if fifo:
        attributes["FifoTopic"] = "true"
    create_topic: dict[str, Any] = {"Name": topic_name, "Attributes": attributes}
    if tags:
        create_topic["Tags"] = [{"Key": k, "Value": v} for k, v in sorted(tags.items())]

    subscriptions = [
        {
            "TopicArn": topic_arn,
            "Protocol": "sqs",
            "Endpoint": arn,
            "Attributes": {"RawMessageDelivery": "true" if raw_message_delivery else "false"},
            "ReturnSubscriptionArn": True,
        }
        for arn in arns
    ]
    queue_policies = {
        arn: {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowSnsTopicSendMessage",
                    "Effect": "Allow",
                    "Principal": {"Service": "sns.amazonaws.com"},
                    "Action": "sqs:SendMessage",
                    "Resource": arn,
                    "Condition": {"ArnEquals": {"aws:SourceArn": topic_arn}},
                }
            ],
        }
        for arn in arns
    }
    return {"create_topic": create_topic, "subscriptions": subscriptions, "queue_policies": queue_policies}
