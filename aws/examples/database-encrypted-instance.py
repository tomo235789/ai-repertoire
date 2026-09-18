"""カード database-encrypted-instance: 保存時暗号化・非公開・マスターパスワードを Secrets Manager 管理にした PostgreSQL

rds.create_db_instance の kwargs を返す。MasterUserPassword は引数にも出力にも存在しない。
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

_IDENTIFIER_RE = re.compile(r"^[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,62}$")
_INSTANCE_CLASS_RE = re.compile(r"^db\.[a-z0-9]+\.[a-z0-9]+$")
_SG_ID_RE = re.compile(r"^sg-[0-9a-f]{8,17}$")
_MASTER_USERNAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,62}$")

MIN_ALLOCATED_STORAGE_GB = 20  # gp3 の PostgreSQL の最小値
RESERVED_USERNAMES = frozenset({"rdsadmin", "admin", "postgres_fdw", "rds_superuser"})


def encrypted_postgres(
    identifier: str,
    instance_class: str,
    allocated_storage: int,
    subnet_group: str,
    security_group_ids: Sequence[str],
    kms_key_id: str | None = None,
    deletion_protection: bool = True,
    *,
    engine_version: str | None = None,
    master_username: str = "app_admin",
    multi_az: bool = False,
    tags: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """create_db_instance の kwargs を返す。

    :param identifier: DB インスタンス識別子（小文字英字始まり、英数字と -、63 文字以内）
    :param instance_class: `db.t4g.micro` のようなインスタンスクラス
    :param allocated_storage: ストレージ GB（20 以上）
    :param subnet_group: プライベートサブネットで構成した DB サブネットグループ名
    :param security_group_ids: `sg-` で始まる VPC セキュリティグループ ID（1 つ以上）
    :param kms_key_id: 暗号化に使う CMK。None なら AWS 管理キー aws/rds（暗号化自体は常に ON）
    :param deletion_protection: 削除保護。既定 True
    """
    if not _IDENTIFIER_RE.match(identifier):
        raise ValueError(f"DB 識別子が不正: {identifier!r}（小文字英字始まり、英数字と -、-- や末尾 - は不可、63 文字以内）")
    if not _INSTANCE_CLASS_RE.match(instance_class):
        raise ValueError(f"インスタンスクラスは db.<family>.<size> の形: {instance_class!r}")
    if isinstance(allocated_storage, bool) or not isinstance(allocated_storage, int) or allocated_storage < MIN_ALLOCATED_STORAGE_GB:
        raise ValueError(f"allocated_storage は {MIN_ALLOCATED_STORAGE_GB} 以上の int（実際: {allocated_storage!r}）")
    if not subnet_group:
        raise ValueError("subnet_group は必須（サブネットグループ無しだとデフォルト VPC に置かれる）")
    sgs = list(security_group_ids)
    if not sgs:
        raise ValueError("security_group_ids は 1 つ以上必要")
    for sg in sgs:
        if not _SG_ID_RE.match(sg):
            raise ValueError(f"セキュリティグループ ID ではない: {sg!r}")
    if not _MASTER_USERNAME_RE.match(master_username) or master_username.lower() in RESERVED_USERNAMES:
        raise ValueError(f"master_username が不正か予約語: {master_username!r}")

    kwargs: dict[str, Any] = {
        "DBInstanceIdentifier": identifier,
        "Engine": "postgres",
        "DBInstanceClass": instance_class,
        "AllocatedStorage": allocated_storage,
        "StorageType": "gp3",
        "StorageEncrypted": True,
        "DBSubnetGroupName": subnet_group,
        "VpcSecurityGroupIds": sgs,
        "PubliclyAccessible": False,
        "MasterUsername": master_username,
        "ManageMasterUserPassword": True,
        "EnableIAMDatabaseAuthentication": True,
        "DeletionProtection": bool(deletion_protection),
        "MultiAZ": bool(multi_az),
        "AutoMinorVersionUpgrade": True,
        "CopyTagsToSnapshot": True,
    }
    if engine_version:
        kwargs["EngineVersion"] = engine_version
    if kms_key_id:
        kwargs["KmsKeyId"] = kms_key_id
        kwargs["MasterUserSecretKmsKeyId"] = kms_key_id
    if tags:
        kwargs["Tags"] = [{"Key": k, "Value": v} for k, v in sorted(tags.items())]
    return kwargs
