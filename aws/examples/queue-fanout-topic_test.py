"""カード queue-fanout-topic の Contract を検証するテスト"""

from __future__ import annotations

import importlib
import json

import pytest

mod = importlib.import_module("queue-fanout-topic")
fanout = mod.fanout

REGION = "us-east-1"
ACCOUNT = "123456789012"
Q1 = "arn:aws:sqs:us-east-1:123456789012:billing"
Q2 = "arn:aws:sqs:us-east-1:123456789012:analytics"
TOPIC_ARN = "arn:aws:sns:us-east-1:123456789012:order-events"


def test_snapshot():
    """出力の全体像"""
    out = fanout("order-events", [Q1, Q2], REGION, ACCOUNT, tags={"env": "prod"})
    assert out == {
        "create_topic": {
            "Name": "order-events",
            "Attributes": {"KmsMasterKeyId": "alias/aws/sns"},
            "Tags": [{"Key": "env", "Value": "prod"}],
        },
        "subscriptions": [
            {
                "TopicArn": TOPIC_ARN,
                "Protocol": "sqs",
                "Endpoint": Q1,
                "Attributes": {"RawMessageDelivery": "true"},
                "ReturnSubscriptionArn": True,
            },
            {
                "TopicArn": TOPIC_ARN,
                "Protocol": "sqs",
                "Endpoint": Q2,
                "Attributes": {"RawMessageDelivery": "true"},
                "ReturnSubscriptionArn": True,
            },
        ],
        "queue_policies": {
            Q1: {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowSnsTopicSendMessage",
                        "Effect": "Allow",
                        "Principal": {"Service": "sns.amazonaws.com"},
                        "Action": "sqs:SendMessage",
                        "Resource": Q1,
                        "Condition": {"ArnEquals": {"aws:SourceArn": TOPIC_ARN}},
                    }
                ],
            },
            Q2: {
                "Version": "2012-10-17",
                "Statement": [
                    {
                        "Sid": "AllowSnsTopicSendMessage",
                        "Effect": "Allow",
                        "Principal": {"Service": "sns.amazonaws.com"},
                        "Action": "sqs:SendMessage",
                        "Resource": Q2,
                        "Condition": {"ArnEquals": {"aws:SourceArn": TOPIC_ARN}},
                    }
                ],
            },
        },
    }
    json.dumps(out)


def test_queue_policy_is_scoped_to_topic_and_send_message_only():
    """各キューポリシーは sqs:SendMessage のみ、Resource は自キュー、SourceArn はこのトピック"""
    out = fanout("order-events", [Q1, Q2], REGION, ACCOUNT)
    assert set(out["queue_policies"]) == {Q1, Q2}
    for arn, policy in out["queue_policies"].items():
        (stmt,) = policy["Statement"]
        assert stmt["Action"] == "sqs:SendMessage"
        assert stmt["Resource"] == arn
        assert stmt["Principal"] == {"Service": "sns.amazonaws.com"}
        assert stmt["Condition"] == {"ArnEquals": {"aws:SourceArn": TOPIC_ARN}}


def test_topic_is_encrypted_by_default_and_accepts_cmk():
    """CMK 未指定でも AWS 管理キーで暗号化し、指定すればそれを使う"""
    assert fanout("t", [Q1], REGION, ACCOUNT)["create_topic"]["Attributes"] == {"KmsMasterKeyId": "alias/aws/sns"}
    out = fanout("t", [Q1], REGION, ACCOUNT, kms_key_id="alias/app-events")
    assert out["create_topic"]["Attributes"]["KmsMasterKeyId"] == "alias/app-events"


def test_raw_message_delivery_flag():
    """raw_message_delivery は文字列 "true"/"false" で購読属性に入る"""
    assert fanout("t", [Q1], REGION, ACCOUNT)["subscriptions"][0]["Attributes"] == {"RawMessageDelivery": "true"}
    out = fanout("t", [Q1], REGION, ACCOUNT, raw_message_delivery=False)
    assert out["subscriptions"][0]["Attributes"] == {"RawMessageDelivery": "false"}


def test_fifo_topic_requires_fifo_queues():
    """.fifo トピックは FifoTopic=true。FIFO と標準の混在は ValueError"""
    fq = "arn:aws:sqs:us-east-1:123456789012:orders.fifo"
    out = fanout("order-events.fifo", [fq], REGION, ACCOUNT)
    assert out["create_topic"]["Attributes"]["FifoTopic"] == "true"
    assert out["subscriptions"][0]["TopicArn"] == "arn:aws:sns:us-east-1:123456789012:order-events.fifo"
    with pytest.raises(ValueError):
        fanout("order-events.fifo", [Q1], REGION, ACCOUNT)
    with pytest.raises(ValueError):
        fanout("order-events", [fq], REGION, ACCOUNT)
    assert "FifoTopic" not in fanout("order-events", [Q1], REGION, ACCOUNT)["create_topic"]["Attributes"]


def test_rejects_empty_duplicate_or_non_sqs_arns():
    """購読先が空、重複、SQS 以外の ARN は ValueError"""
    with pytest.raises(ValueError):
        fanout("t", [], REGION, ACCOUNT)
    with pytest.raises(ValueError):
        fanout("t", [Q1, Q1], REGION, ACCOUNT)
    with pytest.raises(ValueError):
        fanout("t", ["arn:aws:sns:us-east-1:123456789012:other"], REGION, ACCOUNT)
    with pytest.raises(ValueError):
        fanout("t", ["https://sqs.us-east-1.amazonaws.com/123456789012/billing"], REGION, ACCOUNT)


def test_rejects_invalid_topic_name_region_account():
    """トピック名の禁止文字、リージョン・アカウントの形式違いは ValueError"""
    with pytest.raises(ValueError):
        fanout("order events", [Q1], REGION, ACCOUNT)
    with pytest.raises(ValueError):
        fanout("", [Q1], REGION, ACCOUNT)
    with pytest.raises(ValueError):
        fanout("t", [Q1], "US-EAST-1", ACCOUNT)
    with pytest.raises(ValueError):
        fanout("t", [Q1], REGION, "abc")
