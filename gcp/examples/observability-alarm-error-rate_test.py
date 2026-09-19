"""カード observability-alarm-error-rate の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("observability-alarm-error-rate.py")
    spec = importlib.util.spec_from_file_location("observability_alarm_error_rate", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


error_rate_alert = _load().error_rate_alert

CHANNEL = "projects/my-project/notificationChannels/1234567890"


def _cfg(**kw):
    return error_rate_alert("api エラー率", "example-api", [CHANNEL], **kw)


def test_defaults():
    """既定は 5 分の刻みで 5 分間、エラー率 5% 超"""
    cfg = _cfg()
    condition = cfg["conditions"][0]["condition_monitoring_query_language"]
    assert condition["duration"] == "300s"
    assert "condition error_ratio > 0.05" in condition["query"]
    assert cfg["enabled"] is True


def test_channels_sorted_and_deduplicated():
    """通知チャネルは重複を除いて名前順"""
    other = "projects/my-project/notificationChannels/1111111111"
    cfg = error_rate_alert("a", "example-api", [CHANNEL, other, CHANNEL])
    assert cfg["notification_channels"] == sorted({CHANNEL, other})


def test_query_targets_service():
    """クエリは対象サービスで絞る"""
    query = _cfg()["conditions"][0]["condition_monitoring_query_language"]["query"]
    assert "resource.service_name == 'example-api'" in query
    assert "run.googleapis.com/request_count" in query


def test_query_filters_low_traffic():
    """件数が少ない刻みはクエリの段階で落とす"""
    query = _cfg(min_requests_per_interval=50)["conditions"][0][
        "condition_monitoring_query_language"
    ]["query"]
    assert "| filter total >= 50" in query
    assert "failed / total" in query
    # rate() だと毎秒の値になり件数と比べられない
    assert "align delta(" in query
    assert "align rate(" not in query


def test_alert_strategy():
    """自動クローズと、チャネルごとの再通知の間隔が入る"""
    strategy = _cfg()["alert_strategy"]
    assert strategy["auto_close"] == "86400s"
    assert strategy["notification_channel_strategy"] == [
        {"notification_channel_names": [CHANNEL], "renotify_interval": "1800s"}
    ]
    assert "notification_rate_limit" not in strategy


def test_duration_must_be_minute_aligned():
    """継続時間は 60 秒の倍数"""
    with pytest.raises(ValueError, match="60 秒の倍数"):
        _cfg(alignment_seconds=60, duration_seconds=90)


def test_documentation_mentions_threshold():
    """通知本文にしきい値と足切りを書く"""
    content = _cfg(min_requests_per_interval=50)["documentation"]["content"]
    assert "5%" in content
    assert "50 件未満" in content


def test_duration_must_cover_alignment():
    """継続時間は集計の刻み以上"""
    with pytest.raises(ValueError, match="刻み以上"):
        _cfg(alignment_seconds=600, duration_seconds=300)


def test_channels_required():
    """通知先が無いポリシーは作れない"""
    with pytest.raises(ValueError, match="誰も気付かない"):
        error_rate_alert("a", "example-api", [])


def test_service_name_validated_before_embedding():
    """MQL に埋め込む前に Cloud Run の命名規則で検証する"""
    for bad in ("Example-API", "a' or true", "api\nrate", "-api"):
        with pytest.raises(ValueError, match="service_name"):
            error_rate_alert("api エラー率", bad, [CHANNEL])


def test_invalid_inputs():
    """名前・しきい値・刻み・件数・combiner の不正は ValueError"""
    with pytest.raises(ValueError):
        error_rate_alert("", "example-api", [CHANNEL])
    with pytest.raises(ValueError):
        error_rate_alert("a", "", [CHANNEL])
    with pytest.raises(ValueError):
        _cfg(threshold_ratio=0)
    with pytest.raises(ValueError):
        _cfg(threshold_ratio=1.5)
    with pytest.raises(ValueError):
        _cfg(alignment_seconds=120)
    with pytest.raises(ValueError):
        _cfg(min_requests_per_interval=0)
    with pytest.raises(ValueError):
        _cfg(combiner="ANY")


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = _cfg()
    assert a == _cfg()
    assert json.loads(json.dumps(a)) == a
