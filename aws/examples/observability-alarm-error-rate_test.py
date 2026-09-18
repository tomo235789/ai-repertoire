"""カード observability-alarm-error-rate の Contract を検証するテスト"""

from __future__ import annotations

import importlib
import json

import pytest

mod = importlib.import_module("observability-alarm-error-rate")
error_rate_alarm = mod.error_rate_alarm

TOPIC = "arn:aws:sns:us-east-1:123456789012:alerts"
DIMS = {"ApiName": "orders", "Stage": "prod"}


def test_snapshot():
    """出力の全体像"""
    out = error_rate_alarm("orders-5xx-rate", "AWS/ApiGateway", "5XXError", "Count", DIMS, 5, alarm_actions=[TOPIC])
    dims = [{"Name": "ApiName", "Value": "orders"}, {"Name": "Stage", "Value": "prod"}]
    assert out == {
        "AlarmName": "orders-5xx-rate",
        "AlarmDescription": "5XXError / Count が 5% を超えた",
        "ActionsEnabled": True,
        "AlarmActions": [TOPIC],
        "OKActions": [],
        "Metrics": [
            {
                "Id": "errors",
                "MetricStat": {
                    "Metric": {"Namespace": "AWS/ApiGateway", "MetricName": "5XXError", "Dimensions": dims},
                    "Period": 60,
                    "Stat": "Sum",
                },
                "ReturnData": False,
            },
            {
                "Id": "requests",
                "MetricStat": {
                    "Metric": {"Namespace": "AWS/ApiGateway", "MetricName": "Count", "Dimensions": dims},
                    "Period": 60,
                    "Stat": "Sum",
                },
                "ReturnData": False,
            },
            {"Id": "error_rate", "Expression": "errors / requests * 100", "Label": "Error rate (%)", "ReturnData": True},
        ],
        "ComparisonOperator": "GreaterThanThreshold",
        "Threshold": 5.0,
        "EvaluationPeriods": 5,
        "DatapointsToAlarm": 5,
        "TreatMissingData": "notBreaching",
    }
    json.dumps(out)


def test_only_the_rate_expression_returns_data():
    """ReturnData=True は数式 1 つだけ。元の 2 メトリクスは Sum で同じ期間・同じディメンション"""
    out = error_rate_alarm("a", "App", "Errors", "Requests", DIMS, 1, period=300)
    returning = [m for m in out["Metrics"] if m["ReturnData"]]
    assert [m["Id"] for m in returning] == ["error_rate"]
    assert returning[0]["Expression"] == "errors / requests * 100"
    stats = [m["MetricStat"] for m in out["Metrics"] if "MetricStat" in m]
    assert all(s["Stat"] == "Sum" and s["Period"] == 300 for s in stats)
    assert stats[0]["Metric"]["Dimensions"] == stats[1]["Metric"]["Dimensions"]
    assert "MetricName" not in out and "Statistic" not in out  # 単一メトリクス形式と混在させない


def test_missing_data_is_not_breaching():
    """データ欠損（リクエスト 0 で数式が値を返さない場合を含む）では発報しない"""
    assert error_rate_alarm("a", "App", "E", "R", {}, 1)["TreatMissingData"] == "notBreaching"


def test_threshold_boundaries():
    """0 と 100 は許可し float に正規化。範囲外は ValueError、bool や文字列は TypeError"""
    assert error_rate_alarm("a", "App", "E", "R", {}, 0)["Threshold"] == 0.0
    assert error_rate_alarm("a", "App", "E", "R", {}, 100)["Threshold"] == 100.0
    assert error_rate_alarm("a", "App", "E", "R", {}, 2.5)["Threshold"] == 2.5
    for bad in (-0.1, 100.1):
        with pytest.raises(ValueError):
            error_rate_alarm("a", "App", "E", "R", {}, bad)
    with pytest.raises(TypeError):
        error_rate_alarm("a", "App", "E", "R", {}, "5")
    with pytest.raises(TypeError):
        error_rate_alarm("a", "App", "E", "R", {}, True)


def test_period_and_evaluation_rules():
    """period は 10 / 30 / 60 の倍数。datapoints_to_alarm は evaluation_periods 以下"""
    for ok in (10, 30, 60, 300):
        assert error_rate_alarm("a", "App", "E", "R", {}, 1, period=ok)["Metrics"][0]["MetricStat"]["Period"] == ok
    for bad in (0, 45, 90, -60):
        with pytest.raises(ValueError):
            error_rate_alarm("a", "App", "E", "R", {}, 1, period=bad)
    out = error_rate_alarm("a", "App", "E", "R", {}, 1, evaluation_periods=5, datapoints_to_alarm=3)
    assert (out["EvaluationPeriods"], out["DatapointsToAlarm"]) == (5, 3)
    with pytest.raises(ValueError):
        error_rate_alarm("a", "App", "E", "R", {}, 1, evaluation_periods=3, datapoints_to_alarm=4)
    with pytest.raises(ValueError):
        error_rate_alarm("a", "App", "E", "R", {}, 1, evaluation_periods=0)


def test_actions_must_be_arns():
    """通知先は ARN のみ。重複や非 ARN は ValueError。ok_actions も同様"""
    out = error_rate_alarm("a", "App", "E", "R", {}, 1, alarm_actions=[TOPIC], ok_actions=[TOPIC])
    assert out["AlarmActions"] == [TOPIC] and out["OKActions"] == [TOPIC]
    with pytest.raises(ValueError):
        error_rate_alarm("a", "App", "E", "R", {}, 1, alarm_actions=["alerts"])
    with pytest.raises(ValueError):
        error_rate_alarm("a", "App", "E", "R", {}, 1, alarm_actions=[TOPIC, TOPIC])
    with pytest.raises(ValueError):
        error_rate_alarm("a", "App", "E", "R", {}, 1, ok_actions=["alerts"])


def test_rejects_empty_names():
    """アラーム名・名前空間・メトリクス名が空なら ValueError"""
    with pytest.raises(ValueError):
        error_rate_alarm("", "App", "E", "R", {}, 1)
    with pytest.raises(ValueError):
        error_rate_alarm("a", "", "E", "R", {}, 1)
    with pytest.raises(ValueError):
        error_rate_alarm("a", "App", "", "R", {}, 1)
    with pytest.raises(ValueError):
        error_rate_alarm("a", "App", "E", "", {}, 1)
