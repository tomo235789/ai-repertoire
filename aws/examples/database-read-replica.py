"""カード database-read-replica: 読み取り負荷を分散するリードレプリカ

rds.create_db_instance_read_replica の kwargs を返す。ソースを ARN で指定するとクロスリージョン扱いになり、
CMK の指定（KmsKeyId）と SourceRegion が必須になる。
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

_IDENTIFIER_RE = re.compile(r"^[a-z](?:[a-z0-9]|-(?=[a-z0-9])){0,62}$")
_INSTANCE_CLASS_RE = re.compile(r"^db\.[a-z0-9]+\.[a-z0-9]+$")
_RDS_DB_ARN_RE = re.compile(r"^arn:aws(?:-[a-z]+)?:rds:(?P<region>[a-z0-9-]+):\d{12}:db:(?P<id>[a-z][a-z0-9-]*)$")
_SG_ID_RE = re.compile(r"^sg-[0-9a-f]{8,17}$")


def read_replica(
    identifier: str,
    source_identifier_or_arn: str,
    instance_class: str,
    kms_key_id: str | None = None,
    *,
    subnet_group: str | None = None,
    security_group_ids: Sequence[str] | None = None,
    tags: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """create_db_instance_read_replica の kwargs を返す。

    :param identifier: レプリカの DB 識別子
    :param source_identifier_or_arn: 同一リージョンなら識別子、別リージョンならソースの DB ARN
    :param instance_class: レプリカのインスタンスクラス
    :param kms_key_id: クロスリージョンのときだけ必須（レプリカ側リージョンの CMK）。同一リージョンでは指定不可
    :param subnet_group: クロスリージョンでは必須（レプリカ側の DB サブネットグループ）
    :param security_group_ids: レプリカに付ける VPC セキュリティグループ。None ならソースと同じ扱い（同一リージョン）
    """
    if not _IDENTIFIER_RE.match(identifier):
        raise ValueError(f"DB 識別子が不正: {identifier!r}")
    if not _INSTANCE_CLASS_RE.match(instance_class):
        raise ValueError(f"インスタンスクラスは db.<family>.<size> の形: {instance_class!r}")
    if not source_identifier_or_arn:
        raise ValueError("source_identifier_or_arn は必須")

    cross_region = source_identifier_or_arn.startswith("arn:")
    if cross_region:
        m = _RDS_DB_ARN_RE.match(source_identifier_or_arn)
        if not m:
            raise ValueError(f"RDS の DB インスタンス ARN ではない: {source_identifier_or_arn!r}")
        if not kms_key_id:
            raise ValueError("クロスリージョンのレプリカでは kms_key_id（レプリカ側リージョンの CMK）が必須")
        if not subnet_group:
            raise ValueError("クロスリージョンのレプリカでは subnet_group（レプリカ側の DB サブネットグループ）が必須")
        source_id = m["id"]
    else:
        if not _IDENTIFIER_RE.match(source_identifier_or_arn):
            raise ValueError(f"ソースの DB 識別子が不正: {source_identifier_or_arn!r}")
        if kms_key_id:
            raise ValueError("同一リージョンのレプリカはソースと同じ鍵で暗号化される。kms_key_id は指定できない")
        source_id = source_identifier_or_arn
    if source_id == identifier:
        raise ValueError("レプリカの識別子はソースと同じにできない")

    sgs = list(security_group_ids or [])
    for sg in sgs:
        if not _SG_ID_RE.match(sg):
            raise ValueError(f"セキュリティグループ ID ではない: {sg!r}")

    kwargs: dict[str, Any] = {
        "DBInstanceIdentifier": identifier,
        "SourceDBInstanceIdentifier": source_identifier_or_arn,
        "DBInstanceClass": instance_class,
        "PubliclyAccessible": False,
        "AutoMinorVersionUpgrade": True,
        "CopyTagsToSnapshot": True,
    }
    if cross_region:
        kwargs["SourceRegion"] = m["region"]
        kwargs["KmsKeyId"] = kms_key_id
    if subnet_group:
        kwargs["DBSubnetGroupName"] = subnet_group
    if sgs:
        kwargs["VpcSecurityGroupIds"] = sgs
    if tags:
        kwargs["Tags"] = [{"Key": k, "Value": v} for k, v in sorted(tags.items())]
    return kwargs
