"""カード iam-least-privilege-role の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("iam-least-privilege-role.py")
    spec = importlib.util.spec_from_file_location("iam_least_privilege_role", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


least_privilege_role = _load().least_privilege_role

BUCKET_OBJECTS = "arn:aws:s3:::example-bucket/*"


def test_snapshot():
    """信頼ポリシーはサービスの AssumeRole だけ、権限ポリシーは指定 action / resource だけ"""
    cfg = least_privilege_role(
        "example-role",
        "lambda.amazonaws.com",
        actions=["s3:PutObject", "s3:GetObject"],
        resources=[BUCKET_OBJECTS],
    )
    assert cfg == {
        "role_name": "example-role",
        "assume_role_policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {"Service": "lambda.amazonaws.com"},
                    "Action": "sts:AssumeRole",
                }
            ],
        },
        "policy_name": "example-role-policy",
        "policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "LeastPrivilege",
                    "Effect": "Allow",
                    "Action": ["s3:GetObject", "s3:PutObject"],
                    "Resource": [BUCKET_OBJECTS],
                }
            ],
        },
    }
    assert "permissions_boundary" not in cfg
    json.dumps(cfg)


def test_actions_sorted_and_deduplicated():
    """action と resource は重複を除いてソートされる"""
    cfg = least_privilege_role(
        "r", "ecs-tasks.amazonaws.com", ["s3:PutObject", "s3:GetObject", "s3:GetObject"],
        ["arn:aws:s3:::b/*", "arn:aws:s3:::a/*", "arn:aws:s3:::a/*"],
    )
    statement = cfg["policy"]["Statement"][0]
    assert statement["Action"] == ["s3:GetObject", "s3:PutObject"]
    assert statement["Resource"] == ["arn:aws:s3:::a/*", "arn:aws:s3:::b/*"]


def test_only_allow_statements_no_deny_no_star():
    """Allow 文 1 つだけ。Action / Resource に "*" 単体は無い"""
    cfg = least_privilege_role("r", "lambda.amazonaws.com", ["sqs:SendMessage"], ["arn:aws:sqs:us-east-1:123456789012:q"])
    statements = cfg["policy"]["Statement"]
    assert len(statements) == 1 and statements[0]["Effect"] == "Allow"
    assert "*" not in statements[0]["Action"] and "*" not in statements[0]["Resource"]


def test_permissions_boundary_and_source_account():
    """permissions_boundary は ARN をそのまま、source_account は aws:SourceAccount 条件になる"""
    boundary = "arn:aws:iam::123456789012:policy/example-boundary"
    cfg = least_privilege_role(
        "r", "lambda.amazonaws.com", ["s3:GetObject"], [BUCKET_OBJECTS],
        permissions_boundary=boundary, source_account="123456789012",
    )
    assert cfg["permissions_boundary"] == boundary
    assert cfg["assume_role_policy"]["Statement"][0]["Condition"] == {
        "StringEquals": {"aws:SourceAccount": "123456789012"}
    }


@pytest.mark.parametrize("actions", [["*"], ["s3:*"], ["s3:Get*"], ["*:GetObject"], ["GetObject"], []])
def test_wildcard_or_malformed_actions_raise(actions):
    """action の "*"（部分一致も含む）・形式不正・空は ValueError"""
    with pytest.raises(ValueError):
        least_privilege_role("r", "lambda.amazonaws.com", actions, [BUCKET_OBJECTS])


@pytest.mark.parametrize("resources", [["*"], ["example-bucket"], [BUCKET_OBJECTS, "*"], []])
def test_wildcard_or_non_arn_resources_raise(resources):
    """resource の "*" 単体・ARN でないもの・空は ValueError（ARN 内の * は許す）"""
    with pytest.raises(ValueError):
        least_privilege_role("r", "lambda.amazonaws.com", ["s3:GetObject"], resources)


def test_invalid_role_name_service_boundary_account_raise():
    """ロール名・サービスプリンシパル・境界 ARN・アカウント ID の形式不正は ValueError"""
    with pytest.raises(ValueError):
        least_privilege_role("bad name", "lambda.amazonaws.com", ["s3:GetObject"], [BUCKET_OBJECTS])
    with pytest.raises(ValueError):
        least_privilege_role("日本語", "lambda.amazonaws.com", ["s3:GetObject"], [BUCKET_OBJECTS])
    with pytest.raises(ValueError):
        least_privilege_role("r", "lambda", ["s3:GetObject"], [BUCKET_OBJECTS])
    with pytest.raises(ValueError):
        least_privilege_role("r", "lambda.amazonaws.com", ["s3:GetObject"], [BUCKET_OBJECTS], permissions_boundary="example-boundary")
    with pytest.raises(ValueError):
        least_privilege_role("r", "lambda.amazonaws.com", ["s3:GetObject"], [BUCKET_OBJECTS], source_account="12345")


def test_deterministic_and_does_not_mutate_input():
    """同じ入力に同じ出力。入力リストを変更しない"""
    actions = ["s3:PutObject", "s3:GetObject"]
    a = least_privilege_role("r", "lambda.amazonaws.com", actions, [BUCKET_OBJECTS])
    b = least_privilege_role("r", "lambda.amazonaws.com", actions, [BUCKET_OBJECTS])
    assert a == b
    assert actions == ["s3:PutObject", "s3:GetObject"]
