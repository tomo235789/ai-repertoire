"""カード database-backup-retention の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("database-backup-retention.py")
    spec = importlib.util.spec_from_file_location("database_backup_retention", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


backup_retention_config = _load().backup_retention_config


def test_defaults():
    """既定は 35 日保持と地理冗長"""
    cfg = backup_retention_config()
    assert cfg["backup_on_create"] == {
        "backupRetentionDays": 35,
        "geoRedundantBackup": "Enabled",
    }


def test_update_body_omits_creation_only_keys():
    """地理冗長は作成時にしか決められないので、更新用 body には入れない"""
    cfg = backup_retention_config()
    assert cfg["backup_on_update"] == {"backupRetentionDays": 35}
    assert "geoRedundantBackup" not in cfg["backup_on_update"]


def test_geo_redundant_can_be_disabled():
    """地理冗長は切れる"""
    cfg = backup_retention_config(geo_redundant=False)
    assert cfg["backup_on_create"]["geoRedundantBackup"] == "Disabled"


def test_long_term_retention_not_returned():
    """長期保持は Azure Backup のポリシーで設定するので、ここでは返さない"""
    assert set(backup_retention_config()) == {"backup_on_create", "backup_on_update"}


def test_retention_days_range():
    """保持日数は 7〜35 日"""
    for days in (6, 36):
        with pytest.raises(ValueError):
            backup_retention_config(retention_days=days)
    assert backup_retention_config(retention_days=7)["backup_on_create"][
        "backupRetentionDays"
    ] == 7


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = backup_retention_config()
    assert a == backup_retention_config()
    assert json.loads(json.dumps(a)) == a
