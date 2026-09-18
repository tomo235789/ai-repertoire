"""カード secret-kms-key の Contract を検証するテスト"""

from __future__ import annotations

import importlib
import json

import pytest

mod = importlib.import_module("secret-kms-key")
customer_managed_key = mod.customer_managed_key
KEY_ID_PLACEHOLDER = mod.KEY_ID_PLACEHOLDER

ACCOUNT = "123456789012"
ADMIN = "arn:aws:iam::123456789012:role/kms-admin"
USER = "arn:aws:iam::123456789012:role/app-runtime"


def test_snapshot():
    """出力の全体像"""
    out = customer_managed_key("alias/app-data", [ADMIN], [USER], ACCOUNT, 7, description="app data", tags={"env": "prod"})
    assert out == {
        "create_key": {
            "KeyUsage": "ENCRYPT_DECRYPT",
            "KeySpec": "SYMMETRIC_DEFAULT",
            "Origin": "AWS_KMS",
            "MultiRegion": False,
            "BypassPolicyLockoutSafetyCheck": False,
            "Policy": {
                "Version": "2012-10-17",
                "Id": "key-policy-app-data",
                "Statement": [
                    {
                        "Sid": "EnableRootAccountAccess",
                        "Effect": "Allow",
                        "Principal": {"AWS": "arn:aws:iam::123456789012:root"},
                        "Action": "kms:*",
                        "Resource": "*",
                    },
                    {
                        "Sid": "AllowKeyAdministration",
                        "Effect": "Allow",
                        "Principal": {"AWS": [ADMIN]},
                        "Action": mod.ADMIN_ACTIONS,
                        "Resource": "*",
                    },
                    {
                        "Sid": "AllowKeyUsage",
                        "Effect": "Allow",
                        "Principal": {"AWS": [USER]},
                        "Action": ["kms:Encrypt", "kms:Decrypt", "kms:ReEncrypt*", "kms:GenerateDataKey*", "kms:DescribeKey"],
                        "Resource": "*",
                    },
                    {
                        "Sid": "AllowGrantsForAwsResources",
                        "Effect": "Allow",
                        "Principal": {"AWS": [USER]},
                        "Action": ["kms:CreateGrant", "kms:ListGrants", "kms:RevokeGrant"],
                        "Resource": "*",
                        "Condition": {"Bool": {"kms:GrantIsForAWSResource": "true"}},
                    },
                ],
            },
            "Description": "app data",
            "Tags": [{"TagKey": "env", "TagValue": "prod"}],
        },
        "create_alias": {"AliasName": "alias/app-data", "TargetKeyId": "{KeyId}"},
        "enable_key_rotation": {"KeyId": "{KeyId}", "RotationPeriodInDays": 365},
        "schedule_key_deletion": {"KeyId": "{KeyId}", "PendingWindowInDays": 7},
    }
    json.dumps(out)


def test_admin_and_user_permissions_are_separated():
    """管理者は暗号化・復号できず、利用者はポリシー変更・削除予約できない"""
    out = customer_managed_key("alias/app-data", [ADMIN], [USER], ACCOUNT)
    by_sid = {s["Sid"]: s for s in out["create_key"]["Policy"]["Statement"]}
    admin_actions = by_sid["AllowKeyAdministration"]["Action"]
    user_actions = by_sid["AllowKeyUsage"]["Action"]
    for a in ("kms:Encrypt", "kms:Decrypt", "kms:GenerateDataKey*", "kms:ReEncrypt*"):
        assert a not in admin_actions
    for a in ("kms:PutKeyPolicy", "kms:Put*", "kms:ScheduleKeyDeletion", "kms:Delete*", "kms:*"):
        assert a not in user_actions
    assert by_sid["AllowGrantsForAwsResources"]["Condition"] == {"Bool": {"kms:GrantIsForAWSResource": "true"}}


def test_root_access_is_optional_but_requires_admins():
    """root_full_access=False なら root 文が消える。そのとき admin が空なら ValueError"""
    out = customer_managed_key("alias/app-data", [ADMIN], [USER], ACCOUNT, root_full_access=False)
    sids = [s["Sid"] for s in out["create_key"]["Policy"]["Statement"]]
    assert "EnableRootAccountAccess" not in sids
    assert "kms:*" not in json.dumps(out["create_key"]["Policy"])
    with pytest.raises(ValueError):
        customer_managed_key("alias/app-data", [], [USER], ACCOUNT, root_full_access=False)


def test_safe_defaults():
    """対称鍵・単一リージョン・ロックアウト保護 ON・自動ローテーション 365 日・猶予 30 日"""
    out = customer_managed_key("alias/app-data", [ADMIN], [USER], ACCOUNT)
    ck = out["create_key"]
    assert ck["KeySpec"] == "SYMMETRIC_DEFAULT"
    assert ck["MultiRegion"] is False
    assert ck["BypassPolicyLockoutSafetyCheck"] is False
    assert out["enable_key_rotation"]["RotationPeriodInDays"] == 365
    assert out["schedule_key_deletion"]["PendingWindowInDays"] == 30
    assert out["create_alias"]["TargetKeyId"] == KEY_ID_PLACEHOLDER


def test_rejects_invalid_alias():
    """alias/ で始まらない、alias/aws/ で始まる、空はすべて ValueError"""
    for bad in ("app-data", "alias/aws/s3", "alias/", "alias/has space"):
        with pytest.raises(ValueError):
            customer_managed_key(bad, [ADMIN], [USER], ACCOUNT)


def test_rejects_pending_window_out_of_range():
    """猶予は 7〜30 日。範囲外は ValueError、int 以外は TypeError"""
    for bad in (6, 31, 0):
        with pytest.raises(ValueError):
            customer_managed_key("alias/app-data", [ADMIN], [USER], ACCOUNT, bad)
    with pytest.raises(TypeError):
        customer_managed_key("alias/app-data", [ADMIN], [USER], ACCOUNT, 7.0)


def test_rejects_bad_account_and_principals():
    """アカウント ID が 12 桁でない、ARN にワイルドカード、重複は ValueError"""
    with pytest.raises(ValueError):
        customer_managed_key("alias/app-data", [ADMIN], [USER], "12345")
    with pytest.raises(ValueError):
        customer_managed_key("alias/app-data", ["arn:aws:iam::123456789012:role/*"], [USER], ACCOUNT)
    with pytest.raises(ValueError):
        customer_managed_key("alias/app-data", [ADMIN], [USER, USER], ACCOUNT)
