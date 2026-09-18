"""カード database-read-replica の Contract を検証するテスト"""

from __future__ import annotations

import importlib
import json

import pytest

mod = importlib.import_module("database-read-replica")
read_replica = mod.read_replica

SOURCE_ARN = "arn:aws:rds:us-east-1:123456789012:db:app-db"
KEY_WEST = "arn:aws:kms:us-west-2:123456789012:key/11111111-2222-3333-4444-555555555555"
SG = "sg-0123456789abcdef0"


def test_snapshot_same_region():
    """同一リージョン: 識別子指定、KmsKeyId / SourceRegion 無し"""
    out = read_replica("app-db-ro", "app-db", "db.t4g.micro", security_group_ids=[SG], tags={"env": "prod"})
    assert out == {
        "DBInstanceIdentifier": "app-db-ro",
        "SourceDBInstanceIdentifier": "app-db",
        "DBInstanceClass": "db.t4g.micro",
        "PubliclyAccessible": False,
        "AutoMinorVersionUpgrade": True,
        "CopyTagsToSnapshot": True,
        "VpcSecurityGroupIds": [SG],
        "Tags": [{"Key": "env", "Value": "prod"}],
    }
    json.dumps(out)


def test_snapshot_cross_region():
    """クロスリージョン: ARN 指定、SourceRegion をARN から取り、KmsKeyId とサブネットグループを持つ"""
    out = read_replica("app-db-ro", SOURCE_ARN, "db.t4g.micro", KEY_WEST, subnet_group="app-private-west")
    assert out == {
        "DBInstanceIdentifier": "app-db-ro",
        "SourceDBInstanceIdentifier": SOURCE_ARN,
        "DBInstanceClass": "db.t4g.micro",
        "PubliclyAccessible": False,
        "AutoMinorVersionUpgrade": True,
        "CopyTagsToSnapshot": True,
        "SourceRegion": "us-east-1",
        "KmsKeyId": KEY_WEST,
        "DBSubnetGroupName": "app-private-west",
    }
    json.dumps(out)


def test_never_public():
    """どちらの形でも PubliclyAccessible は False"""
    assert read_replica("r", "s", "db.t4g.micro")["PubliclyAccessible"] is False
    assert read_replica("r", SOURCE_ARN, "db.t4g.micro", KEY_WEST, subnet_group="g")["PubliclyAccessible"] is False


def test_cross_region_requires_kms_key_and_subnet_group():
    """ARN 指定で kms_key_id か subnet_group が無いと ValueError"""
    with pytest.raises(ValueError, match="kms_key_id"):
        read_replica("r", SOURCE_ARN, "db.t4g.micro", subnet_group="g")
    with pytest.raises(ValueError, match="subnet_group"):
        read_replica("r", SOURCE_ARN, "db.t4g.micro", KEY_WEST)


def test_same_region_rejects_kms_key():
    """同一リージョンで kms_key_id を渡すと ValueError（ソースと同じ鍵になるため）"""
    with pytest.raises(ValueError):
        read_replica("r", "s", "db.t4g.micro", KEY_WEST)


def test_rejects_same_identifier_as_source():
    """レプリカ名がソースと同じなら ValueError（識別子・ARN の両方）"""
    with pytest.raises(ValueError):
        read_replica("app-db", "app-db", "db.t4g.micro")
    with pytest.raises(ValueError):
        read_replica("app-db", SOURCE_ARN, "db.t4g.micro", KEY_WEST, subnet_group="g")


def test_rejects_invalid_inputs():
    """不正な識別子、RDS 以外の ARN、クラス形式違い、SG 形式違いは ValueError"""
    with pytest.raises(ValueError):
        read_replica("App", "s", "db.t4g.micro")
    with pytest.raises(ValueError):
        read_replica("r", "arn:aws:rds:us-east-1:123456789012:cluster:app", "db.t4g.micro", KEY_WEST, subnet_group="g")
    with pytest.raises(ValueError):
        read_replica("r", "s", "t4g.micro")
    with pytest.raises(ValueError):
        read_replica("r", "s", "db.t4g.micro", security_group_ids=["app-sg"])
    with pytest.raises(ValueError):
        read_replica("r", "", "db.t4g.micro")
