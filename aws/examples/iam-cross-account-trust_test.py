"""カード iam-cross-account-trust の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("iam-cross-account-trust.py")
    spec = importlib.util.spec_from_file_location("iam_cross_account_trust", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cross_account_trust = _load().cross_account_trust


def test_snapshot_default():
    """root プリンシパル + ExternalId 条件 + セッション上限 1 時間"""
    cfg = cross_account_trust(["123456789012"], "example-external-id")
    assert cfg == {
        "assume_role_policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "CrossAccountAssumeRole",
                    "Effect": "Allow",
                    "Principal": {"AWS": ["arn:aws:iam::123456789012:root"]},
                    "Action": "sts:AssumeRole",
                    "Condition": {
                        "StringEquals": {"sts:ExternalId": "example-external-id"},
                        "NumericLessThanEqualsIfExists": {"sts:DurationSeconds": "3600"},
                    },
                }
            ],
        },
        "max_session_duration": 3600,
    }
    json.dumps(cfg)


def test_multiple_accounts_sorted_and_deduplicated():
    """複数アカウントはソート・重複除去して root ARN にする"""
    cfg = cross_account_trust(["210987654321", "123456789012", "123456789012"], "example-external-id")
    assert cfg["assume_role_policy"]["Statement"][0]["Principal"]["AWS"] == [
        "arn:aws:iam::123456789012:root",
        "arn:aws:iam::210987654321:root",
    ]


def test_external_id_condition_always_present():
    """sts:ExternalId の StringEquals 条件が必ず入る"""
    condition = cross_account_trust(["123456789012"], "abc")["assume_role_policy"]["Statement"][0]["Condition"]
    assert condition["StringEquals"] == {"sts:ExternalId": "abc"}


def test_session_bounds_and_mfa():
    """3600〜43200 秒を受け付け、ポリシー側にも上限を入れる。require_mfa で MFA 条件を追加"""
    cfg = cross_account_trust(["123456789012"], "abc", max_session_seconds=43200, require_mfa=True)
    assert cfg["max_session_duration"] == 43200
    condition = cfg["assume_role_policy"]["Statement"][0]["Condition"]
    assert condition["NumericLessThanEqualsIfExists"] == {"sts:DurationSeconds": "43200"}
    assert condition["Bool"] == {"aws:MultiFactorAuthPresent": "true"}
    assert "Bool" not in cross_account_trust(["123456789012"], "abc")["assume_role_policy"]["Statement"][0]["Condition"]


@pytest.mark.parametrize("seconds", [3599, 43201, 0, -1, 3600.0, True])
def test_session_out_of_range_raises(seconds):
    """セッション秒数の範囲外・非 int は ValueError"""
    with pytest.raises(ValueError):
        cross_account_trust(["123456789012"], "abc", max_session_seconds=seconds)


@pytest.mark.parametrize("account_ids", [[], ["12345678901"], ["1234567890123"], ["12345678901a"], ["arn:aws:iam::123456789012:root"]])
def test_invalid_account_ids_raise(account_ids):
    """空、12 桁でない、数字以外を含む、ARN 形式のアカウント ID は ValueError"""
    with pytest.raises(ValueError):
        cross_account_trust(account_ids, "abc")


@pytest.mark.parametrize("external_id", ["", "a", "has space", "x" * 1225, "日本語"])
def test_invalid_external_id_raises(external_id):
    """ExternalId は 2〜1224 文字の [A-Za-z0-9_+=,.@:/-]"""
    with pytest.raises(ValueError):
        cross_account_trust(["123456789012"], external_id)


def test_deterministic():
    """同じ入力に同じ出力"""
    assert cross_account_trust(["123456789012"], "abc") == cross_account_trust(["123456789012"], "abc")
