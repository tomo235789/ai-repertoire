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


fifo_queue_with_dlq = _load().fifo_queue_with_dlq


def test_session_required_for_ordering():
    """順序保証はセッション必須で実現する"""
    assert fifo_queue_with_dlq("orders")["requiresSession"] is True


def test_dead_lettering_on_expiration():
    """期限切れのメッセージも配信不能キューへ送る"""
    props = fifo_queue_with_dlq("orders")
    assert props["deadLetteringOnMessageExpiration"] is True
    assert props["maxDeliveryCount"] == 5


def test_durations_are_iso8601():
    """期間は ISO 8601 の duration 文字列で入る"""
    props = fifo_queue_with_dlq("orders", lock_seconds=90, message_ttl_seconds=86400)
    assert props["lockDuration"] == "PT1M30S"
    assert props["defaultMessageTimeToLive"] == "P1D"
    assert props["duplicateDetectionHistoryTimeWindow"] == "PT10M"


def test_duplicate_detection_window_range():
    """窓は 0（無効）か 20 秒〜7 日"""
    with pytest.raises(ValueError, match="重複検出の窓"):
        fifo_queue_with_dlq("orders", duplicate_detection_seconds=19)
    with pytest.raises(ValueError, match="重複検出の窓"):
        fifo_queue_with_dlq("orders", duplicate_detection_seconds=7 * 86400 + 1)
    props = fifo_queue_with_dlq("orders", duplicate_detection_seconds=20)
    assert props["duplicateDetectionHistoryTimeWindow"] == "PT20S"


def test_duplicate_detection_can_be_disabled():
    """窓を 0 にすると重複検出を使わず、窓のキーも入らない"""
    props = fifo_queue_with_dlq("orders", duplicate_detection_seconds=0)
    assert props["requiresDuplicateDetection"] is False
    assert "duplicateDetectionHistoryTimeWindow" not in props


def test_partitioning_disabled():
    """パーティション分割はセッションの順序と相性が悪いので無効"""
    assert fifo_queue_with_dlq("orders")["enablePartitioning"] is False


def test_lock_seconds_range():
    """ロック時間は 1〜300 秒"""
    with pytest.raises(ValueError, match="ロック時間"):
        fifo_queue_with_dlq("orders", lock_seconds=0)
    with pytest.raises(ValueError, match="ロック時間"):
        fifo_queue_with_dlq("orders", lock_seconds=301)
    assert fifo_queue_with_dlq("orders", lock_seconds=300)["lockDuration"] == "PT5M"


def test_ttl_must_exceed_duplicate_window():
    """メッセージの寿命は重複検出の窓より長くする"""
    with pytest.raises(ValueError, match="長くする"):
        fifo_queue_with_dlq("orders", message_ttl_seconds=600, duplicate_detection_seconds=600)


def test_size_limited_to_supported_values():
    """キューの容量は対応値だけ"""
    with pytest.raises(ValueError, match="最大サイズ"):
        fifo_queue_with_dlq("orders", max_size_megabytes=1)
    assert fifo_queue_with_dlq("orders", max_size_megabytes=5120)["maxSizeInMegabytes"] == 5120


def test_invalid_inputs():
    """名前・配信回数・サイズの不正は ValueError"""
    with pytest.raises(ValueError):
        fifo_queue_with_dlq("-orders")
    with pytest.raises(ValueError):
        fifo_queue_with_dlq("orders", max_delivery_count=0)
    with pytest.raises(ValueError):
        fifo_queue_with_dlq("orders", max_size_megabytes=0)


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = fifo_queue_with_dlq("orders")
    assert a == fifo_queue_with_dlq("orders")
    assert json.loads(json.dumps(a)) == a
