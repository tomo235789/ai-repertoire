"""カード secret-rotation の Contract を検証するテスト"""

from __future__ import annotations

import importlib
import json

import pytest

mod = importlib.import_module("secret-rotation")
rotation_config = mod.rotation_config

LAMBDA = "arn:aws:lambda:us-east-1:123456789012:function:rotate-db-secret"


def test_snapshot():
    """出力の全体像"""
    out = rotation_config("app/prod/db", LAMBDA, 30)
    assert out == {
        "SecretId": "app/prod/db",
        "RotationLambdaARN": LAMBDA,
        "RotationRules": {"ScheduleExpression": "rate(30 days)"},
        "RotateImmediately": False,
    }
    json.dumps(out)


def test_schedule_expression_uses_singular_for_one_day():
    """1 日なら rate(1 day)、それ以外は複数形"""
    assert rotation_config("s", LAMBDA, 1)["RotationRules"] == {"ScheduleExpression": "rate(1 day)"}
    assert rotation_config("s", LAMBDA, 365)["RotationRules"] == {"ScheduleExpression": "rate(365 days)"}


def test_does_not_set_automatically_after_days():
    """ScheduleExpression と排他の AutomaticallyAfterDays は出さない"""
    assert "AutomaticallyAfterDays" not in rotation_config("s", LAMBDA, 7)["RotationRules"]


def test_rotate_immediately_defaults_false_and_can_be_enabled():
    """既定では即時ローテーションしない"""
    assert rotation_config("s", LAMBDA, 7)["RotateImmediately"] is False
    assert rotation_config("s", LAMBDA, 7, rotate_immediately=True)["RotateImmediately"] is True


def test_rejects_days_out_of_range():
    """0、366、負数は ValueError。bool や小数は TypeError"""
    for bad in (0, 366, -1):
        with pytest.raises(ValueError):
            rotation_config("s", LAMBDA, bad)
    with pytest.raises(TypeError):
        rotation_config("s", LAMBDA, 7.5)
    with pytest.raises(TypeError):
        rotation_config("s", LAMBDA, True)


def test_rejects_non_lambda_arn_and_empty_secret():
    """Lambda 以外の ARN や空の secret_id は ValueError"""
    with pytest.raises(ValueError):
        rotation_config("s", "arn:aws:iam::123456789012:role/x", 7)
    with pytest.raises(ValueError):
        rotation_config("s", "rotate-db-secret", 7)
    with pytest.raises(ValueError):
        rotation_config("", LAMBDA, 7)
