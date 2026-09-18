"""カード observability-structured-logs の Contract を検証するテスト"""

from __future__ import annotations

import importlib
import json

import pytest

mod = importlib.import_module("observability-structured-logs")
log_group_with_error_metric = mod.log_group_with_error_metric

KEY = "arn:aws:kms:us-east-1:123456789012:key/11111111-2222-3333-4444-555555555555"


def test_snapshot():
    """出力の全体像"""
    out = log_group_with_error_metric("/app/api", 30, KEY, tags={"env": "prod"})
    assert out == {
        "create_log_group": {
            "logGroupName": "/app/api",
            "logGroupClass": "STANDARD",
            "kmsKeyId": KEY,
            "tags": {"env": "prod"},
        },
        "put_retention_policy": {"logGroupName": "/app/api", "retentionInDays": 30},
        "put_metric_filter": {
            "logGroupName": "/app/api",
            "filterName": "ErrorCountFilter",
            "filterPattern": '{ $.level = "error" }',
            "metricTransformations": [
                {
                    "metricName": "ErrorCount",
                    "metricNamespace": "Application",
                    "metricValue": "1",
                    "defaultValue": 0.0,
                    "unit": "Count",
                }
            ],
        },
    }
    json.dumps(out)


def test_same_log_group_name_in_all_three_calls():
    """3 つの kwargs すべてが同じロググループ名を指す"""
    out = log_group_with_error_metric("/app/api", 7)
    names = {out[k]["logGroupName"] for k in ("create_log_group", "put_retention_policy", "put_metric_filter")}
    assert names == {"/app/api"}


def test_kms_is_optional_but_must_be_key_arn():
    """kms 未指定なら kmsKeyId を出さない。エイリアスや鍵 ID は ValueError"""
    assert "kmsKeyId" not in log_group_with_error_metric("/app/api", 7)["create_log_group"]
    for bad in ("alias/app-logs", "11111111-2222-3333-4444-555555555555", "arn:aws:kms:us-east-1:123456789012:alias/x"):
        with pytest.raises(ValueError):
            log_group_with_error_metric("/app/api", 7, bad)


def test_error_metric_counts_one_per_match_and_zero_when_absent():
    """メトリクス値は 1、defaultValue は 0（一致が無い期間も 0 として記録される）"""
    (mt,) = log_group_with_error_metric("/app/api", 7)["put_metric_filter"]["metricTransformations"]
    assert mt["metricValue"] == "1"
    assert mt["defaultValue"] == 0.0
    assert mt["unit"] == "Count"


def test_custom_pattern_namespace_and_metric_name():
    """パターン・名前空間・メトリクス名は差し替えられる"""
    out = log_group_with_error_metric(
        "/app/api", 7, error_pattern='{ $.severity = "ERROR" }', metric_namespace="MyApp/API", metric_name="Errors"
    )
    pmf = out["put_metric_filter"]
    assert pmf["filterPattern"] == '{ $.severity = "ERROR" }'
    assert pmf["filterName"] == "ErrorsFilter"
    assert pmf["metricTransformations"][0]["metricNamespace"] == "MyApp/API"
    assert pmf["metricTransformations"][0]["metricName"] == "Errors"


def test_retention_must_be_an_allowed_value():
    """許容値以外（2、10、31、0、負数、bool）は ValueError"""
    for bad in (2, 10, 31, 0, -1, True):
        with pytest.raises(ValueError):
            log_group_with_error_metric("/app/api", bad)
    for ok in (1, 3653):
        assert log_group_with_error_metric("/app/api", ok)["put_retention_policy"]["retentionInDays"] == ok


def test_rejects_invalid_name_pattern_namespace():
    """禁止文字のロググループ名、空パターン、AWS/ 名前空間、不正なメトリクス名は ValueError"""
    with pytest.raises(ValueError):
        log_group_with_error_metric("/app api", 7)
    with pytest.raises(ValueError):
        log_group_with_error_metric("", 7)
    with pytest.raises(ValueError):
        log_group_with_error_metric("/app/api", 7, error_pattern="   ")
    with pytest.raises(ValueError):
        log_group_with_error_metric("/app/api", 7, metric_namespace="AWS/Lambda")
    with pytest.raises(ValueError):
        log_group_with_error_metric("/app/api", 7, metric_namespace="")
    with pytest.raises(ValueError):
        log_group_with_error_metric("/app/api", 7, metric_name="has space")
