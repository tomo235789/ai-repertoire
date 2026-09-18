"""カード queue-fanout-topic の Contract を検証するテスト"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("queue-fanout-topic.py")
    spec = importlib.util.spec_from_file_location("queue_fanout_topic", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fanout_topic = _load().fanout_topic

SUBS = {"billing": "eventType = 'OrderPlaced'", "audit": None}


def test_topic_defaults():
    """トピックは重複検出あり、パーティション分割あり、順序保証なし"""
    topic = fanout_topic("orders", SUBS)["topic"]
    assert topic["defaultMessageTimeToLive"] == "P14D"
    assert topic["requiresDuplicateDetection"] is True
    assert topic["duplicateDetectionHistoryTimeWindow"] == "P1D"
    assert topic["enablePartitioning"] is True
    assert topic["supportOrdering"] is False


def test_subscriptions_sorted_and_dead_lettered():
    """サブスクリプションは名前順。期限切れもフィルタ例外も退避する"""
    subs = fanout_topic("orders", SUBS)["subscriptions"]
    assert list(subs) == ["audit", "billing"]
    props = subs["audit"]["properties"]
    assert props["deadLetteringOnMessageExpiration"] is True
    assert props["deadLetteringOnFilterEvaluationExceptions"] is True


def test_filter_rule_only_when_expression_given():
    """フィルタ式を渡した購読者だけルールを持ち、既定ルールを消す指示が入る"""
    subs = fanout_topic("orders", SUBS)["subscriptions"]
    assert subs["audit"]["rule"] is None
    assert subs["audit"]["default_rule_to_delete"] is None
    assert subs["billing"]["default_rule_to_delete"] == "$Default"
    rule = subs["billing"]["rule"]
    assert rule["name"] == "billing-filter"
    assert rule["properties"]["filterType"] == "SqlFilter"
    assert rule["properties"]["sqlFilter"]["sqlExpression"] == "eventType = 'OrderPlaced'"


def test_duplicate_detection_window_range():
    """窓は 0〜7 日"""
    with pytest.raises(ValueError, match="重複検出の窓"):
        fanout_topic("orders", SUBS, message_ttl_days=14, duplicate_detection_days=8)


def test_subscription_name_length():
    """サブスクリプション名は 50 文字まで"""
    long_name = "a" * 51
    with pytest.raises(ValueError, match="サブスクリプション名"):
        fanout_topic("orders", {long_name: None})
    short = fanout_topic("orders", {"a": None})
    assert list(short["subscriptions"]) == ["a"]


def test_duplicate_detection_can_be_disabled():
    """窓を 0 にすると重複検出を使わず、窓のキーも入らない"""
    topic = fanout_topic("orders", SUBS, duplicate_detection_days=0)["topic"]
    assert topic["requiresDuplicateDetection"] is False
    assert "duplicateDetectionHistoryTimeWindow" not in topic


def test_duplicate_window_shorter_than_ttl():
    """重複検出の窓はメッセージの寿命より短くする"""
    with pytest.raises(ValueError, match="短くする"):
        fanout_topic("orders", SUBS, message_ttl_days=1, duplicate_detection_days=1)


def test_filter_expression_rejects_semicolon():
    """フィルタ式に ; は使えない"""
    with pytest.raises(ValueError, match="; は使えない"):
        fanout_topic("orders", {"billing": "a = 1; drop"})


def test_invalid_inputs():
    """名前・購読者・寿命・配信回数の不正は ValueError"""
    with pytest.raises(ValueError):
        fanout_topic("-orders", SUBS)
    with pytest.raises(ValueError):
        fanout_topic("orders", {})
    with pytest.raises(ValueError):
        fanout_topic("orders", {"-bad": None})
    with pytest.raises(ValueError):
        fanout_topic("orders", SUBS, max_delivery_count=0)


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    subs = dict(SUBS)
    before = copy.deepcopy(subs)
    cfg = fanout_topic("orders", subs)
    assert subs == before
    assert json.loads(json.dumps(cfg)) == cfg
