"""カード storage-bucket-private の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("storage-bucket-private.py")
    spec = importlib.util.spec_from_file_location("storage_bucket_private", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


private_bucket_config = _load().private_bucket_config


def test_snapshot_default():
    """既定値: SSE-S3、公開ブロック 4 つ、ACL 無効、TLS 必須。tagging は無い"""
    cfg = private_bucket_config("example-bucket")
    assert cfg == {
        "create_bucket": {"Bucket": "example-bucket", "ObjectOwnership": "BucketOwnerEnforced"},
        "public_access_block": {
            "Bucket": "example-bucket",
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        },
        "encryption": {
            "Bucket": "example-bucket",
            "ServerSideEncryptionConfiguration": {
                "Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]
            },
        },
        "ownership": {
            "Bucket": "example-bucket",
            "OwnershipControls": {"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]},
        },
        "policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "DenyInsecureTransport",
                    "Effect": "Deny",
                    "Principal": "*",
                    "Action": "s3:*",
                    "Resource": ["arn:aws:s3:::example-bucket", "arn:aws:s3:::example-bucket/*"],
                    "Condition": {"Bool": {"aws:SecureTransport": "false"}},
                }
            ],
        },
    }
    assert "tagging" not in cfg
    json.dumps(cfg)


def test_all_public_access_blocked():
    """公開ブロックは 4 項目すべて True"""
    block = private_bucket_config("example-bucket")["public_access_block"]["PublicAccessBlockConfiguration"]
    assert set(block) == {"BlockPublicAcls", "IgnorePublicAcls", "BlockPublicPolicy", "RestrictPublicBuckets"}
    assert all(block.values())


def test_kms_encryption_with_bucket_key():
    """kms_key_id を渡すと aws:kms + KMSMasterKeyID、Bucket Key 有効"""
    key = "arn:aws:kms:us-east-1:123456789012:key/00000000-0000-0000-0000-000000000000"
    rule = private_bucket_config("example-bucket", kms_key_id=key)["encryption"][
        "ServerSideEncryptionConfiguration"
    ]["Rules"][0]
    assert rule == {
        "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms", "KMSMasterKeyID": key},
        "BucketKeyEnabled": True,
    }


def test_policy_only_denies_and_requires_tls():
    """ポリシーは Deny 文だけで、Allow は含まない"""
    policy = private_bucket_config("example-bucket")["policy"]
    assert [s["Effect"] for s in policy["Statement"]] == ["Deny"]
    assert policy["Statement"][0]["Condition"] == {"Bool": {"aws:SecureTransport": "false"}}


def test_tags_sorted_by_key():
    """tags はキー順の TagSet になる"""
    cfg = private_bucket_config("example-bucket", tags={"env": "dev", "app": "example"})
    assert cfg["tagging"] == {
        "Bucket": "example-bucket",
        "Tagging": {"TagSet": [{"Key": "app", "Value": "example"}, {"Key": "env", "Value": "dev"}]},
    }
    assert "tagging" not in private_bucket_config("example-bucket", tags={})


def test_region_location_constraint():
    """us-east-1 以外は LocationConstraint を付け、us-east-1 と未指定では付けない"""
    tokyo = private_bucket_config("example-bucket", region="ap-northeast-1")["create_bucket"]
    assert tokyo["CreateBucketConfiguration"] == {"LocationConstraint": "ap-northeast-1"}
    assert "CreateBucketConfiguration" not in private_bucket_config("example-bucket", region="us-east-1")["create_bucket"]
    assert "CreateBucketConfiguration" not in private_bucket_config("example-bucket")["create_bucket"]


def test_deterministic_and_pure():
    """同じ入力に同じ出力。入力の tags を変更しない"""
    tags = {"env": "dev"}
    a = private_bucket_config("example-bucket", tags=tags)
    b = private_bucket_config("example-bucket", tags=tags)
    assert a == b and a is not b
    assert tags == {"env": "dev"}


@pytest.mark.parametrize(
    "name",
    ["Example", "ab", "a" * 64, "has_underscore", "-leading", "trailing.", "double..dot", "192.168.0.1"],
)
def test_invalid_bucket_name_raises(name):
    """S3 の命名規則に反する名前は ValueError"""
    with pytest.raises(ValueError):
        private_bucket_config(name)


def test_invalid_kms_key_and_tags_raise():
    """空の KMS キー ID、長すぎるタグは ValueError"""
    with pytest.raises(ValueError):
        private_bucket_config("example-bucket", kms_key_id="  ")
    with pytest.raises(ValueError):
        private_bucket_config("example-bucket", tags={"k" * 129: "v"})
    with pytest.raises(ValueError):
        private_bucket_config("example-bucket", tags={"k": "v" * 257})
    with pytest.raises(ValueError):
        private_bucket_config("example-bucket", tags={f"k{i}": "v" for i in range(51)})
