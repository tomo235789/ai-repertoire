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

SCOPE = (
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
    "/providers/Microsoft.Insights/components/example-ai"
)
ACTION = (
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
    "/providers/Microsoft.Insights/actionGroups/example-ag"
)


def _cfg(**kw):
    return error_rate_alert("error-rate", SCOPE, ACTION, **kw)


def test_defaults():
    """既定は 15 分の集計、5 分ごとの評価、5% で発報"""
    cfg = _cfg()
    assert cfg["windowSize"] == "PT15M"
    assert cfg["evaluationFrequency"] == "PT5M"
    assert cfg["criteria"]["allOf"][0]["threshold"] == 5.0
    assert cfg["criteria"]["allOf"][0]["operator"] == "GreaterThan"


def test_hour_durations():
    """60 分単位の期間は時間で表す"""
    cfg = _cfg(window_minutes=120, evaluation_minutes=60)
    assert cfg["windowSize"] == "PT2H"
    assert cfg["evaluationFrequency"] == "PT1H"


def test_query_filters_low_traffic():
    """件数が少ない期間は評価しないクエリになる"""
    query = _cfg(min_requests=50)["criteria"]["allOf"][0]["query"]
    assert "| where total >= 50" in query
    assert "ago(15m)" in query
    assert "errorRate" in query


def test_scope_and_action_group():
    """監視対象と通知先はそのまま入る"""
    cfg = _cfg()
    assert cfg["scopes"] == [SCOPE]
    assert cfg["actions"]["actionGroups"] == [ACTION]


def test_auto_mitigate_default():
    """回復したら自動で解決扱いにする"""
    assert _cfg()["autoMitigate"] is True
    assert _cfg(auto_mitigate=False)["autoMitigate"] is False


def test_evaluation_must_not_exceed_window():
    """評価間隔は集計期間以下"""
    with pytest.raises(ValueError, match="集計期間以下"):
        _cfg(window_minutes=5, evaluation_minutes=15)


def test_arm_id_must_be_complete():
    """接頭辞だけの ARM ID は通さない"""
    partial = "/subscriptions/00000000-0000-0000-0000-000000000000"
    with pytest.raises(ValueError, match="scope_id"):
        error_rate_alert("error-rate", partial, ACTION)
    with pytest.raises(ValueError, match="action_group_id"):
        error_rate_alert("error-rate", SCOPE, partial)


def test_integer_parameters_checked():
    """小数を渡すと ISO 8601 の duration が壊れるので弾く"""
    with pytest.raises(ValueError, match="window_minutes"):
        _cfg(window_minutes=15.0)
    with pytest.raises(ValueError, match="severity"):
        _cfg(severity=True)


def test_invalid_inputs():
    """名前・ARM ID・しきい値・期間・件数・重大度の不正は ValueError"""
    with pytest.raises(ValueError):
        error_rate_alert("", SCOPE, ACTION)
    with pytest.raises(ValueError):
        error_rate_alert("a", "example-ai", ACTION)
    with pytest.raises(ValueError):
        _cfg(threshold_percent=0)
    with pytest.raises(ValueError):
        _cfg(threshold_percent=101)
    with pytest.raises(ValueError):
        _cfg(window_minutes=7)
    with pytest.raises(ValueError):
        _cfg(min_requests=0)
    with pytest.raises(ValueError):
        _cfg(severity=5)


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = _cfg()
    assert a == _cfg()
    assert json.loads(json.dumps(a)) == a
