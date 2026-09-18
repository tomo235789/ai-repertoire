"""カード iam-read-only-policy の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("iam-read-only-policy.py")
    spec = importlib.util.spec_from_file_location("iam_read_only_policy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load()
read_only_policy = _mod.read_only_policy
SECRET_REVEALING_ACTIONS = _mod.SECRET_REVEALING_ACTIONS


def test_snapshot():
    """Allow 文 1 つに、ソート済みの action と resource"""
    policy = read_only_policy(
        ["s3:ListBucket", "s3:GetObject"],
        ["arn:aws:s3:::example-bucket/*", "arn:aws:s3:::example-bucket"],
    )
    assert policy == {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "ReadOnly",
                "Effect": "Allow",
                "Action": ["s3:GetObject", "s3:ListBucket"],
                "Resource": ["arn:aws:s3:::example-bucket", "arn:aws:s3:::example-bucket/*"],
            }
        ],
    }
    json.dumps(policy)


def test_accepts_get_list_describe_and_trailing_wildcard():
    """Get* / List* / Describe* と、その末尾ワイルドカードを許可する。resource は "*" も可"""
    policy = read_only_policy(["ec2:DescribeInstances", "s3:Get*", "sqs:ListQueues"], ["*"])
    assert policy["Statement"][0]["Action"] == ["ec2:DescribeInstances", "s3:Get*", "sqs:ListQueues"]
    assert policy["Statement"][0]["Resource"] == ["*"]


@pytest.mark.parametrize(
    "action",
    ["s3:PutObject", "s3:DeleteObject", "s3:*", "*", "iam:PassRole", "*:GetObject", "s3:get*", "s3:Getobject:x", "GetObject"],
)
def test_non_read_actions_raise(action):
    """Get* / List* / Describe* 以外の action は ValueError（大文字小文字も区別）"""
    with pytest.raises(ValueError):
        read_only_policy([action], ["*"])


@pytest.mark.parametrize("action", sorted(SECRET_REVEALING_ACTIONS))
def test_secret_revealing_get_actions_raise(action):
    """名前は Get* でも秘密値や一時資格情報を返す action は ValueError"""
    with pytest.raises(ValueError):
        read_only_policy([action], ["*"])


def test_empty_or_non_arn_raise():
    """action / resource が空、resource が ARN でも "*" でもない場合は ValueError"""
    with pytest.raises(ValueError):
        read_only_policy([], ["*"])
    with pytest.raises(ValueError):
        read_only_policy(["s3:GetObject"], [])
    with pytest.raises(ValueError):
        read_only_policy(["s3:GetObject"], ["example-bucket"])


def test_deduplicated_and_deterministic():
    """重複を除き、同じ入力に同じ出力"""
    a = read_only_policy(["s3:GetObject", "s3:GetObject"], ["*", "*"])
    assert a["Statement"][0]["Action"] == ["s3:GetObject"]
    assert a["Statement"][0]["Resource"] == ["*"]
    assert a == read_only_policy(["s3:GetObject"], ["*"])
