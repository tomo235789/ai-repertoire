"""カード storage-bucket-private: 公開アクセスを禁止した S3 バケットの設定を組み立てる純粋関数。

boto3 の各 API にそのまま渡せる kwargs を返す。API は呼ばない。
"""

from __future__ import annotations

import re
from typing import Any, Mapping

_BUCKET_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]$")
_IPV4_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")


def _validate_bucket_name(name: str) -> None:
    """S3 のバケット命名規則（小文字英数字・ドット・ハイフン、3〜63 文字）"""
    if not _BUCKET_NAME_RE.match(name) or ".." in name or _IPV4_RE.match(name):
        raise ValueError(f"invalid bucket name: {name!r}")


def _validate_tags(tags: Mapping[str, str]) -> None:
    if len(tags) > 50:
        raise ValueError("S3 bucket tags must be 50 or fewer")
    for key, value in tags.items():
        if not key or len(key) > 128 or len(value) > 256:
            raise ValueError(f"invalid tag: {key!r}={value!r}")


def _encryption_rule(kms_key_id: str | None) -> dict[str, Any]:
    if kms_key_id is None:
        return {"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}
    if not kms_key_id.strip():
        raise ValueError("kms_key_id must not be empty")
    return {
        "ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "aws:kms", "KMSMasterKeyID": kms_key_id},
        "BucketKeyEnabled": True,
    }


def _tls_only_policy(name: str) -> dict[str, Any]:
    """HTTP（aws:SecureTransport=false）の全操作を拒否するバケットポリシー"""
    return {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "DenyInsecureTransport",
                "Effect": "Deny",
                "Principal": "*",
                "Action": "s3:*",
                "Resource": [f"arn:aws:s3:::{name}", f"arn:aws:s3:::{name}/*"],
                "Condition": {"Bool": {"aws:SecureTransport": "false"}},
            }
        ],
    }


def private_bucket_config(
    name: str,
    kms_key_id: str | None = None,
    tags: Mapping[str, str] | None = None,
    region: str | None = None,
) -> dict[str, Any]:
    """公開アクセスを禁止し、既定で暗号化する S3 バケットの設定を返す。

    返り値の各キーは boto3 S3 クライアントの API に対応する:
      create_bucket        -> create_bucket(**...)
      public_access_block  -> put_public_access_block(**...)
      encryption           -> put_bucket_encryption(**...)
      ownership            -> put_bucket_ownership_controls(**...)
      policy               -> put_bucket_policy(Bucket=name, Policy=json.dumps(...))
      tagging              -> put_bucket_tagging(**...)（tags を渡したときだけ）

    region が us-east-1 以外なら create_bucket に LocationConstraint を付ける。
    """
    _validate_bucket_name(name)
    create_bucket: dict[str, Any] = {"Bucket": name, "ObjectOwnership": "BucketOwnerEnforced"}
    if region is not None and region != "us-east-1":
        create_bucket["CreateBucketConfiguration"] = {"LocationConstraint": region}

    config: dict[str, Any] = {
        "create_bucket": create_bucket,
        "public_access_block": {
            "Bucket": name,
            "PublicAccessBlockConfiguration": {
                "BlockPublicAcls": True,
                "IgnorePublicAcls": True,
                "BlockPublicPolicy": True,
                "RestrictPublicBuckets": True,
            },
        },
        "encryption": {
            "Bucket": name,
            "ServerSideEncryptionConfiguration": {"Rules": [_encryption_rule(kms_key_id)]},
        },
        "ownership": {
            "Bucket": name,
            "OwnershipControls": {"Rules": [{"ObjectOwnership": "BucketOwnerEnforced"}]},
        },
        "policy": _tls_only_policy(name),
    }
    if tags:
        _validate_tags(tags)
        config["tagging"] = {
            "Bucket": name,
            "Tagging": {"TagSet": [{"Key": k, "Value": tags[k]} for k in sorted(tags)]},
        }
    return config
