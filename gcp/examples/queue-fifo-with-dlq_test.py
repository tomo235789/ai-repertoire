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


PROJECT_NUMBER = "123456789012"


def _full(**kw):
    kwargs = {"subscription_project_number": PROJECT_NUMBER}
    kwargs.update(kw)
    return ordered_subscription_with_dlq(TOPIC, SUB, DLQ, **kwargs)


def _cfg(**kw):
    return _full(**kw)["subscription_config"]


def test_dead_letter_bindings_split_by_phase():
    """購読への権限は購読ができてからでないと与えられないので、前後に分ける"""
    cfg = _full()
    agent = "serviceAccount:service-123456789012@gcp-sa-pubsub.iam.gserviceaccount.com"
    assert cfg["bindings_before_create"] == [
        {"resource": DLQ, "role": "roles/pubsub.publisher", "members": [agent]}
    ]
    assert cfg["bindings_after_create"] == [
        {"resource": SUB, "role": "roles/pubsub.subscriber", "members": [agent]}
    ]


def test_project_number_must_be_digits():
    """プロジェクト番号は数字"""
    with pytest.raises(ValueError, match="プロジェクト番号"):
        ordered_subscription_with_dlq(TOPIC, SUB, DLQ, subscription_project_number="my-project")


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
        ordered_subscription_with_dlq(TOPIC, SUB, TOPIC, subscription_project_number=PROJECT_NUMBER)


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
        ordered_subscription_with_dlq("orders", SUB, DLQ, subscription_project_number=PROJECT_NUMBER)
    with pytest.raises(ValueError):
        ordered_subscription_with_dlq(
            TOPIC, "projects/my-project/subscriptions/1bad", DLQ,
            subscription_project_number=PROJECT_NUMBER,
        )
    with pytest.raises(ValueError):
        ordered_subscription_with_dlq(
            TOPIC, TOPIC, DLQ, subscription_project_number=PROJECT_NUMBER
        )  # 購読の位置にトピック
    with pytest.raises(ValueError):
        ordered_subscription_with_dlq(
            SUB, SUB, DLQ, subscription_project_number=PROJECT_NUMBER
        )  # トピックの位置に購読
    with pytest.raises(ValueError):
        ordered_subscription_with_dlq(
            "projects/my-project", SUB, DLQ, subscription_project_number=PROJECT_NUMBER
        )


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = _full()
    assert a == _full()
    assert json.loads(json.dumps(a)) == a
