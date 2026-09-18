"""カード secret-fetch-at-runtime の Contract を検証するテスト"""

from __future__ import annotations

import importlib
import json

import pytest

mod = importlib.import_module("secret-fetch-at-runtime")
secret_and_read_policy = mod.secret_and_read_policy

ROLE = "arn:aws:iam::123456789012:role/app-runtime"
KEY = "arn:aws:kms:us-east-1:123456789012:key/11111111-2222-3333-4444-555555555555"


def test_snapshot():
    """出力の全体像"""
    out = secret_and_read_policy("app/prod/db", KEY, [ROLE], description="DB 接続情報", tags={"env": "prod"})
    assert out == {
        "create_secret": {
            "Name": "app/prod/db",
            "Description": "DB 接続情報",
            "KmsKeyId": KEY,
            "Tags": [{"Key": "env", "Value": "prod"}],
        },
        "read_policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowReadersGetSecretValue",
                    "Effect": "Allow",
                    "Principal": {"AWS": [ROLE]},
                    "Action": "secretsmanager:GetSecretValue",
                    "Resource": "*",
                },
                {
                    "Sid": "DenyGetSecretValueToOthers",
                    "Effect": "Deny",
                    "Principal": {"AWS": "*"},
                    "Action": "secretsmanager:GetSecretValue",
                    "Resource": "*",
                    "Condition": {"ArnNotEquals": {"aws:PrincipalArn": [ROLE]}},
                },
            ],
        },
    }
    json.dumps(out)


def test_secret_value_is_never_in_output():
    """SecretString / SecretBinary は出力に含まれず、引数でも受け取らない"""
    out = secret_and_read_policy("app/prod/db", reader_principal_arns=[ROLE])
    assert "SecretString" not in out["create_secret"]
    assert "SecretBinary" not in out["create_secret"]
    with pytest.raises(TypeError):
        secret_and_read_policy("app/prod/db", reader_principal_arns=[ROLE], SecretString="x")


def test_default_uses_aws_managed_key_and_minimal_kwargs():
    """kms_key_id を省略すると KmsKeyId を渡さず（AWS 管理キー）、Name だけになる"""
    out = secret_and_read_policy("app/prod/db", reader_principal_arns=[ROLE])
    assert out["create_secret"] == {"Name": "app/prod/db"}


def test_read_policy_allows_only_get_secret_value_to_listed_principals():
    """Allow は GetSecretValue のみ、Deny が一覧外のプリンシパルを弾く"""
    other = "arn:aws:iam::123456789012:role/other"
    out = secret_and_read_policy("app/prod/db", reader_principal_arns=[ROLE, other])
    allow, deny = out["read_policy"]["Statement"]
    assert allow["Effect"] == "Allow"
    assert allow["Action"] == "secretsmanager:GetSecretValue"
    assert allow["Principal"] == {"AWS": [ROLE, other]}
    assert deny["Effect"] == "Deny"
    assert deny["Condition"] == {"ArnNotEquals": {"aws:PrincipalArn": [ROLE, other]}}
    for stmt in out["read_policy"]["Statement"]:
        assert stmt["Action"] == "secretsmanager:GetSecretValue"


def test_rejects_empty_or_wildcard_readers():
    """読み手が空、ワイルドカード、IAM 以外の ARN、重複は ValueError"""
    with pytest.raises(ValueError):
        secret_and_read_policy("app/prod/db", reader_principal_arns=[])
    with pytest.raises(ValueError):
        secret_and_read_policy("app/prod/db", reader_principal_arns=["*"])
    with pytest.raises(ValueError):
        secret_and_read_policy("app/prod/db", reader_principal_arns=["arn:aws:iam::123456789012:role/*"])
    with pytest.raises(ValueError):
        secret_and_read_policy("app/prod/db", reader_principal_arns=["arn:aws:sqs:us-east-1:123456789012:q"])
    with pytest.raises(ValueError):
        secret_and_read_policy("app/prod/db", reader_principal_arns=[ROLE, ROLE])


def test_rejects_invalid_name():
    """名前に使えない文字や空文字は ValueError"""
    with pytest.raises(ValueError):
        secret_and_read_policy("", reader_principal_arns=[ROLE])
    with pytest.raises(ValueError):
        secret_and_read_policy("app prod", reader_principal_arns=[ROLE])
    with pytest.raises(ValueError):
        secret_and_read_policy("a" * 513, reader_principal_arns=[ROLE])
