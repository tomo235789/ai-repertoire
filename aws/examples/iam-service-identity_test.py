"""カード iam-service-identity の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("iam-service-identity.py")
    spec = importlib.util.spec_from_file_location("iam_service_identity", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


service_identity_trust = _load().service_identity_trust

OIDC_ARN = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
HOST = "token.actions.githubusercontent.com"


def test_service_snapshot_without_conditions():
    """service: sts:AssumeRole のみ。conditions 無しなら Condition キーも無い"""
    policy = service_identity_trust("service", "lambda.amazonaws.com")
    assert policy == {
        "Version": "2012-10-17",
        "Statement": [
            {"Effect": "Allow", "Principal": {"Service": "lambda.amazonaws.com"}, "Action": "sts:AssumeRole"}
        ],
    }
    json.dumps(policy)


def test_service_conditions_source_account_and_arn():
    """aws:SourceAccount は StringEquals、ワイルドカード付き aws:SourceArn は ArnLike"""
    policy = service_identity_trust(
        "service",
        "events.amazonaws.com",
        {"aws:SourceArn": "arn:aws:events:us-east-1:123456789012:rule/*", "aws:SourceAccount": "123456789012"},
    )
    assert policy["Statement"][0]["Condition"] == {
        "StringEquals": {"aws:SourceAccount": "123456789012"},
        "ArnLike": {"aws:SourceArn": "arn:aws:events:us-east-1:123456789012:rule/*"},
    }
    exact = service_identity_trust("service", "events.amazonaws.com", {"aws:SourceArn": "arn:aws:events:us-east-1:123456789012:rule/x"})
    assert exact["Statement"][0]["Condition"] == {"StringEquals": {"aws:SourceArn": "arn:aws:events:us-east-1:123456789012:rule/x"}}


def test_oidc_snapshot():
    """oidc: Federated プリンシパルに AssumeRoleWithWebIdentity、sub / aud を StringEquals で要求"""
    policy = service_identity_trust(
        "oidc", OIDC_ARN, {"sub": "repo:example-org/example-repo:ref:refs/heads/main", "aud": "sts.amazonaws.com"}
    )
    assert policy == {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {"Federated": OIDC_ARN},
                "Action": "sts:AssumeRoleWithWebIdentity",
                "Condition": {
                    "StringEquals": {
                        f"{HOST}:aud": "sts.amazonaws.com",
                        f"{HOST}:sub": "repo:example-org/example-repo:ref:refs/heads/main",
                    }
                },
            }
        ],
    }
    assert list(policy["Statement"][0]["Condition"]["StringEquals"]) == [f"{HOST}:aud", f"{HOST}:sub"]
    json.dumps(policy)


def test_oidc_wildcard_sub_uses_string_like_and_prefixed_keys_accepted():
    """sub に * があれば StringLike。"<host>:sub" 形式のキーもそのまま使える。複数値はソート済みリスト"""
    policy = service_identity_trust(
        "oidc", OIDC_ARN, {f"{HOST}:sub": ["repo:example-org/b:*", "repo:example-org/a:*"], "aud": "sts.amazonaws.com"}
    )
    assert policy["Statement"][0]["Condition"] == {
        "StringEquals": {f"{HOST}:aud": "sts.amazonaws.com"},
        "StringLike": {f"{HOST}:sub": ["repo:example-org/a:*", "repo:example-org/b:*"]},
    }


@pytest.mark.parametrize(
    "conditions",
    [{}, {"sub": "repo:example-org/example-repo:*"}, {"aud": "sts.amazonaws.com"}, {"sub": "x", "aud": "*"}, {"sub": "", "aud": "sts.amazonaws.com"}],
)
def test_oidc_requires_sub_and_exact_aud(conditions):
    """sub / aud が無い、aud にワイルドカード、空の値は ValueError"""
    with pytest.raises(ValueError):
        service_identity_trust("oidc", OIDC_ARN, conditions)


def test_invalid_principals_and_kind_raise():
    """種別の不正、サービスでないプリンシパル、OIDC プロバイダ ARN でないものは ValueError"""
    with pytest.raises(ValueError):
        service_identity_trust("account", "123456789012")
    with pytest.raises(ValueError):
        service_identity_trust("service", "lambda")
    with pytest.raises(ValueError):
        service_identity_trust("oidc", "arn:aws:iam::123456789012:saml-provider/x", {"sub": "a", "aud": "b"})
    with pytest.raises(ValueError):
        service_identity_trust("oidc", "arn:aws:iam::123456789012:oidc-provider/", {"sub": "a", "aud": "b"})
    with pytest.raises(ValueError):
        service_identity_trust("service", "lambda.amazonaws.com", {"sts:ExternalId": "x"})


def test_deterministic():
    """同じ入力に同じ出力"""
    args = ("oidc", OIDC_ARN, {"sub": "repo:example-org/example-repo:*", "aud": "sts.amazonaws.com"})
    assert service_identity_trust(*args) == service_identity_trust(*args)
