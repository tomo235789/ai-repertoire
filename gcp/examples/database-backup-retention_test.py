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
    """既定は 18:00 開始、30 世代、ポイントインタイム復旧あり"""
    cfg = backup_retention_config()
    assert cfg["enabled"] is True
    assert cfg["startTime"] == "18:00"
    assert cfg["pointInTimeRecoveryEnabled"] is True
    assert cfg["transactionLogRetentionDays"] == 7


def test_retention_is_by_count():
    """保持は日数ではなく世代数で指定する"""
    settings = backup_retention_config(retained_backups=60)["backupRetentionSettings"]
    assert settings == {"retentionUnit": "COUNT", "retainedBackups": 60}


def test_log_retention_only_with_pitr():
    """ポイントインタイム復旧を切るとログ保持のキーは入らない"""
    cfg = backup_retention_config(point_in_time_recovery=False)
    assert cfg["pointInTimeRecoveryEnabled"] is False
    assert "transactionLogRetentionDays" not in cfg
    with pytest.raises(ValueError, match="切るなら"):
        backup_retention_config(point_in_time_recovery=False, transaction_log_retention_days=3)


def test_location_is_opt_in():
    """保存先は渡したときだけ入る"""
    assert "location" not in backup_retention_config()
    assert backup_retention_config(location="asia")["location"] == "asia"


def test_time_format():
    """開始時刻は 24 時間表記の HH:MM"""
    assert backup_retention_config(start_time="03:30")["startTime"] == "03:30"
    for bad in ("3:30", "24:00", "18:60", "18時"):
        with pytest.raises(ValueError):
            backup_retention_config(start_time=bad)


def test_range_checks():
    """保持数とログ保持日数の範囲外は ValueError"""
    for kwargs in (
        {"retained_backups": 6},
        {"retained_backups": 366},
        {"transaction_log_retention_days": 0},
        {"transaction_log_retention_days": 8},
    ):
        with pytest.raises(ValueError):
            backup_retention_config(**kwargs)


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = backup_retention_config()
    assert a == backup_retention_config()
    assert json.loads(json.dumps(a)) == a
