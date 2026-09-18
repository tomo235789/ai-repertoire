"""カード queue-fifo-with-dlq の Contract を検証するテスト"""

from __future__ import annotations

import importlib
import json

import pytest

mod = importlib.import_module("queue-fifo-with-dlq")
fifo_queue_with_dlq = mod.fifo_queue_with_dlq

REGION = "us-east-1"
ACCOUNT = "123456789012"


def test_snapshot():
    """出力の全体像"""
    out = fifo_queue_with_dlq("orders.fifo", REGION, ACCOUNT, tags={"env": "prod"})
    assert out == {
        "dlq": {
            "QueueName": "orders-dlq.fifo",
            "Attributes": {
                "FifoQueue": "true",
                "MessageRetentionPeriod": "1209600",
                "SqsManagedSseEnabled": "true",
            },
            "tags": {"env": "prod"},
        },
        "queue": {
            "QueueName": "orders.fifo",
            "Attributes": {
                "FifoQueue": "true",
                "VisibilityTimeout": "30",
                "RedrivePolicy": '{"deadLetterTargetArn": "arn:aws:sqs:us-east-1:123456789012:orders-dlq.fifo", "maxReceiveCount": 5}',
                "SqsManagedSseEnabled": "true",
            },
            "tags": {"env": "prod"},
        },
    }
    json.dumps(out)


def test_both_queues_are_fifo_and_encrypted():
    """DLQ もメインも FifoQueue=true で SSE が有効。属性値はすべて文字列"""
    out = fifo_queue_with_dlq("orders.fifo", REGION, ACCOUNT)
    for key in ("dlq", "queue"):
        attrs = out[key]["Attributes"]
        assert attrs["FifoQueue"] == "true"
        assert attrs["SqsManagedSseEnabled"] == "true"
        assert all(isinstance(v, str) for v in attrs.values())


def test_kms_key_replaces_managed_sse():
    """kms_key_id を渡すと KmsMasterKeyId になり SqsManagedSseEnabled は出さない"""
    out = fifo_queue_with_dlq("orders.fifo", REGION, ACCOUNT, kms_key_id="alias/app-data")
    for key in ("dlq", "queue"):
        attrs = out[key]["Attributes"]
        assert attrs["KmsMasterKeyId"] == "alias/app-data"
        assert "SqsManagedSseEnabled" not in attrs


def test_redrive_policy_is_json_string_pointing_to_dlq():
    """RedrivePolicy は JSON 文字列。DLQ の ARN と maxReceiveCount を持つ"""
    out = fifo_queue_with_dlq("orders.fifo", REGION, ACCOUNT, max_receive_count=3, visibility_timeout=120)
    redrive = json.loads(out["queue"]["Attributes"]["RedrivePolicy"])
    assert redrive == {"deadLetterTargetArn": "arn:aws:sqs:us-east-1:123456789012:orders-dlq.fifo", "maxReceiveCount": 3}
    assert out["queue"]["Attributes"]["VisibilityTimeout"] == "120"
    assert "RedrivePolicy" not in out["dlq"]["Attributes"]
    assert out["dlq"]["Attributes"]["MessageRetentionPeriod"] == str(14 * 24 * 60 * 60)


def test_content_based_deduplication_is_opt_in():
    """既定では ContentBasedDeduplication を出さず、True のときだけ付く"""
    assert "ContentBasedDeduplication" not in fifo_queue_with_dlq("q.fifo", REGION, ACCOUNT)["queue"]["Attributes"]
    out = fifo_queue_with_dlq("q.fifo", REGION, ACCOUNT, content_based_deduplication=True)
    assert out["queue"]["Attributes"]["ContentBasedDeduplication"] == "true"
    assert "ContentBasedDeduplication" not in out["dlq"]["Attributes"]


def test_rejects_non_fifo_or_invalid_names():
    """.fifo で終わらない、使えない文字、長すぎる名前は ValueError"""
    for bad in ("orders", "orders.FIFO", "orders queue.fifo", "a" * 76 + ".fifo", ".fifo"):
        with pytest.raises(ValueError):
            fifo_queue_with_dlq(bad, REGION, ACCOUNT)


def test_rejects_out_of_range_values_and_bad_region_account():
    """maxReceiveCount / visibility の範囲外、リージョン・アカウントの形式違いは ValueError"""
    with pytest.raises(ValueError):
        fifo_queue_with_dlq("q.fifo", REGION, ACCOUNT, max_receive_count=0)
    with pytest.raises(ValueError):
        fifo_queue_with_dlq("q.fifo", REGION, ACCOUNT, max_receive_count=1001)
    with pytest.raises(ValueError):
        fifo_queue_with_dlq("q.fifo", REGION, ACCOUNT, visibility_timeout=-1)
    with pytest.raises(ValueError):
        fifo_queue_with_dlq("q.fifo", REGION, ACCOUNT, visibility_timeout=43201)
    with pytest.raises(ValueError):
        fifo_queue_with_dlq("q.fifo", "useast1", ACCOUNT)
    with pytest.raises(ValueError):
        fifo_queue_with_dlq("q.fifo", REGION, "1234")
