"""カード storage-bucket-private: 公開アクセスを禁止した Cloud Storage バケットの設定を組み立てる。

google-cloud-storage の Client.create_bucket に渡すバケットのプロパティと、
Bucket.set_iam_policy に渡す IAM ポリシーを dict で返す純粋関数。API は呼ばない。
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

# バケット名は 3〜63 文字の小文字英数字・ハイフン・アンダースコア・ドット。先頭末尾は英数字
_BUCKET_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]$")
_PROJECT_RE = re.compile(r"^[a-z][a-z0-9-]{4,28}[a-z0-9]$")
_KMS_KEY_RE = re.compile(r"^projects/[^/]+/locations/[^/]+/keyRings/[^/]+/cryptoKeys/[^/]+$")
_MEMBER_RE = re.compile(r"^(user|serviceAccount|group):[^\s:]+$")

# 公開を意味するメンバー。誤って渡されたら弾く
PUBLIC_MEMBERS = frozenset({"allUsers", "allAuthenticatedUsers"})
READER_ROLE = "roles/storage.objectViewer"


def private_bucket_config(
    name: str,
    location: str,
    *,
    project: str,
    kms_key_name: str | None = None,
    reader_members: Sequence[str] = (),
    labels: Mapping[str, str] | None = None,
    retention_period_seconds: int | None = None,
) -> dict[str, Any]:
    """公開アクセスを禁止したバケットの設定と IAM ポリシーを組み立てる。

    返り値は {"bucket": create_bucket のプロパティ, "iam_policy": set_iam_policy の引数}。
    """
    if not _BUCKET_NAME_RE.fullmatch(name):
        raise ValueError(f"バケット名が Cloud Storage の命名規則に合わない: {name!r}")
    if "goog" in name:
        raise ValueError(f"バケット名に goog を含められない: {name!r}")
    if not _PROJECT_RE.fullmatch(project):
        raise ValueError(f"プロジェクト ID の形式が不正: {project!r}")
    if not location:
        raise ValueError("location は必須（例: asia-northeast1）")
    if kms_key_name is not None and not _KMS_KEY_RE.fullmatch(kms_key_name):
        raise ValueError(f"CMEK は projects/.../cryptoKeys/... の形式にする: {kms_key_name!r}")
    if retention_period_seconds is not None and retention_period_seconds <= 0:
        raise ValueError("retention_period_seconds は正の整数にする")

    members = list(dict.fromkeys(reader_members))  # 重複を除いて順序は保つ
    for member in members:
        if member in PUBLIC_MEMBERS:
            raise ValueError(f"公開メンバーは許可しない: {member}（公開配信は cdn-static-site を使う）")
        if not _MEMBER_RE.fullmatch(member):
            raise ValueError(f"メンバーは user: / serviceAccount: / group: で始める: {member!r}")

    bucket: dict[str, Any] = {
        "name": name,
        "project": project,
        "location": location.lower(),
        # 均一なバケットレベルアクセス。ACL を無効にして IAM だけで権限を決める
        "iam_configuration": {
            "uniform_bucket_level_access": {"enabled": True},
            "public_access_prevention": "enforced",
        },
        "storage_class": "STANDARD",
        "versioning": {"enabled": True},
    }
    if kms_key_name is not None:
        bucket["encryption"] = {"default_kms_key_name": kms_key_name}
    if labels:
        bucket["labels"] = dict(sorted(labels.items()))
    if retention_period_seconds is not None:
        bucket["retention_policy"] = {"retention_period": retention_period_seconds}

    bindings = []
    if members:
        bindings.append({"role": READER_ROLE, "members": members})

    return {"bucket": bucket, "iam_policy": {"version": 3, "bindings": bindings}}
