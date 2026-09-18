"""カード queue-fifo-with-dlq の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("queue-fifo-with-dlq.py")
    spec = importlib.util.spec_from_file_location("queue_fifo_with_dlq", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ordered_subscription_with_dlq = _load().ordered_subscription_with_dlq

TOPIC = "projects/my-project/topics/orders"
SUB = "projects/my-project/subscriptions/orders-worker"
DLQ = "projects/my-project/topics/orders-dead-letter"


def _cfg(**kw):
    return ordered_subscription_with_dlq(TOPIC, SUB, DLQ, **kw)["subscription_config"]


def test_ordering_and_exactly_once():
    """順序保証と一度だけの配信が既定で有効"""
    cfg = _cfg()
    assert cfg["enable_message_ordering"] is True
    assert cfg["enable_exactly_once_delivery"] is True
    assert _cfg(enable_exactly_once=False)["enable_exactly_once_delivery"] is False


def test_dead_letter_policy():
    """試行回数を超えたら配信不能トピックへ送る"""
    policy = _cfg()["dead_letter_policy"]
    assert policy == {"dead_letter_topic": DLQ, "max_delivery_attempts": 5}


def test_retry_policy_backoff():
    """再試行は指数バックオフの範囲を明示する"""
    retry = _cfg()["retry_policy"]
    assert retry["minimum_backoff"] == {"seconds": 10}
    assert retry["maximum_backoff"] == {"seconds": 600}


def test_retention_in_seconds():
    """保持期間は秒で渡す"""
    assert _cfg()["message_retention_duration"] == {"seconds": 7 * 86400}
    assert _cfg(message_retention_days=1)["message_retention_duration"] == {"seconds": 86400}


def test_filter_is_opt_in():
    """フィルタは渡したときだけ入る"""
    assert "filter" not in _cfg()
    assert _cfg(filter_expression='attributes.type = "order"')["filter"] == (
        'attributes.type = "order"'
    )


def test_dead_letter_must_differ_from_topic():
    """配信不能トピックを購読元と同じにできない"""
    with pytest.raises(ValueError, match="循環"):
        ordered_subscription_with_dlq(TOPIC, SUB, TOPIC)


def test_range_checks():
    """確認応答の期限・試行回数・保持日数の範囲外は ValueError"""
    for kwargs in (
        {"ack_deadline_seconds": 9},
        {"ack_deadline_seconds": 601},
        {"max_delivery_attempts": 4},
        {"max_delivery_attempts": 101},
        {"message_retention_days": 0},
        {"message_retention_days": 8},
    ):
        with pytest.raises(ValueError):
            _cfg(**kwargs)


def test_names_must_be_fully_qualified():
    """種別まで含めた完全名でないと ValueError"""
    with pytest.raises(ValueError):
        ordered_subscription_with_dlq("orders", SUB, DLQ)
    with pytest.raises(ValueError):
        ordered_subscription_with_dlq(TOPIC, "projects/my-project/subscriptions/1bad", DLQ)
    with pytest.raises(ValueError):
        ordered_subscription_with_dlq(TOPIC, TOPIC, DLQ)  # 購読の位置にトピック
    with pytest.raises(ValueError):
        ordered_subscription_with_dlq(SUB, SUB, DLQ)  # トピックの位置に購読
    with pytest.raises(ValueError):
        ordered_subscription_with_dlq("projects/my-project", SUB, DLQ)


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = ordered_subscription_with_dlq(TOPIC, SUB, DLQ)
    assert a == ordered_subscription_with_dlq(TOPIC, SUB, DLQ)
    assert json.loads(json.dumps(a)) == a
