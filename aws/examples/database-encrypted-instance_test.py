"""カード database-encrypted-instance の Contract を検証するテスト"""

from __future__ import annotations

import importlib
import json

import pytest

mod = importlib.import_module("database-encrypted-instance")
encrypted_postgres = mod.encrypted_postgres

KEY = "arn:aws:kms:us-east-1:123456789012:key/11111111-2222-3333-4444-555555555555"
SG = "sg-0123456789abcdef0"


def test_snapshot():
    """出力の全体像"""
    out = encrypted_postgres("app-db", "db.t4g.micro", 20, "app-private", [SG], KEY, engine_version="16", tags={"env": "prod"})
    assert out == {
        "DBInstanceIdentifier": "app-db",
        "Engine": "postgres",
        "DBInstanceClass": "db.t4g.micro",
        "AllocatedStorage": 20,
        "StorageType": "gp3",
        "StorageEncrypted": True,
        "DBSubnetGroupName": "app-private",
        "VpcSecurityGroupIds": [SG],
        "PubliclyAccessible": False,
        "MasterUsername": "app_admin",
        "ManageMasterUserPassword": True,
        "EnableIAMDatabaseAuthentication": True,
        "DeletionProtection": True,
        "MultiAZ": False,
        "AutoMinorVersionUpgrade": True,
        "CopyTagsToSnapshot": True,
        "EngineVersion": "16",
        "KmsKeyId": KEY,
        "MasterUserSecretKmsKeyId": KEY,
        "Tags": [{"Key": "env", "Value": "prod"}],
    }
    json.dumps(out)


def test_safe_defaults():
    """暗号化 ON・非公開・削除保護 ON・パスワードは Secrets Manager 管理"""
    out = encrypted_postgres("app-db", "db.t4g.micro", 20, "app-private", [SG])
    assert out["StorageEncrypted"] is True
    assert out["PubliclyAccessible"] is False
    assert out["DeletionProtection"] is True
    assert out["ManageMasterUserPassword"] is True
    assert "KmsKeyId" not in out  # AWS 管理キー aws/rds


def test_master_password_is_never_accepted_or_emitted():
    """MasterUserPassword は引数に無く（TypeError）、出力にも含まれない"""
    out = encrypted_postgres("app-db", "db.t4g.micro", 20, "app-private", [SG])
    assert "MasterUserPassword" not in out
    with pytest.raises(TypeError):
        encrypted_postgres("app-db", "db.t4g.micro", 20, "app-private", [SG], MasterUserPassword="x")
    with pytest.raises(TypeError):
        encrypted_postgres("app-db", "db.t4g.micro", 20, "app-private", [SG], master_password="x")


def test_deletion_protection_can_be_disabled_explicitly():
    """deletion_protection=False を明示したときだけ削除保護が外れる"""
    out = encrypted_postgres("app-db", "db.t4g.micro", 20, "app-private", [SG], deletion_protection=False)
    assert out["DeletionProtection"] is False
    assert out["StorageEncrypted"] is True


def test_cmk_is_applied_to_both_storage_and_master_secret():
    """kms_key_id を渡すとストレージとマスターシークレットの両方に同じ鍵を使う"""
    out = encrypted_postgres("app-db", "db.t4g.micro", 20, "app-private", [SG], kms_key_id=KEY)
    assert out["KmsKeyId"] == KEY
    assert out["MasterUserSecretKmsKeyId"] == KEY


def test_rejects_invalid_identifier():
    """大文字、数字始まり、連続ハイフン、末尾ハイフン、64 文字は ValueError"""
    for bad in ("App-DB", "1db", "app--db", "app-db-", "a" * 64, ""):
        with pytest.raises(ValueError):
            encrypted_postgres(bad, "db.t4g.micro", 20, "app-private", [SG])


def test_rejects_small_storage_bad_class_missing_network():
    """ストレージ 20 未満、db. で始まらないクラス、サブネットグループ無し、SG 無し・不正は ValueError"""
    with pytest.raises(ValueError):
        encrypted_postgres("app-db", "db.t4g.micro", 19, "app-private", [SG])
    with pytest.raises(ValueError):
        encrypted_postgres("app-db", "t4g.micro", 20, "app-private", [SG])
    with pytest.raises(ValueError):
        encrypted_postgres("app-db", "db.t4g.micro", 20, "", [SG])
    with pytest.raises(ValueError):
        encrypted_postgres("app-db", "db.t4g.micro", 20, "app-private", [])
    with pytest.raises(ValueError):
        encrypted_postgres("app-db", "db.t4g.micro", 20, "app-private", ["app-sg"])


def test_rejects_reserved_master_username():
    """PostgreSQL / RDS の予約ユーザー名は ValueError"""
    for bad in ("rdsadmin", "admin", "rds_superuser", "1abc", "app-admin"):
        with pytest.raises(ValueError):
            encrypted_postgres("app-db", "db.t4g.micro", 20, "app-private", [SG], master_username=bad)
