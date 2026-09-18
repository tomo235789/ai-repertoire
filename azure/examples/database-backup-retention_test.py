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
    assert cfg["backup"] == {"backupRetentionDays": 35, "geoRedundantBackup": "Enabled"}


def test_long_term_retention_off_by_default():
    """長期保持は既定で無効。期間は PT0S で表す"""
    ltr = backup_retention_config()["long_term_retention"]
    assert ltr == {
        "weeklyRetention": "PT0S",
        "monthlyRetention": "PT0S",
        "yearlyRetention": "PT0S",
        "weekOfYear": 0,
    }


def test_long_term_retention_durations():
    """週次・月次・年次は ISO 8601 の duration になる"""
    ltr = backup_retention_config(
        weekly_retention_weeks=12,
        monthly_retention_months=12,
        yearly_retention_years=5,
        week_of_year_for_yearly=26,
    )["long_term_retention"]
    assert ltr["weeklyRetention"] == "P12W"
    assert ltr["monthlyRetention"] == "P12M"
    assert ltr["yearlyRetention"] == "P5Y"
    assert ltr["weekOfYear"] == 26


def test_week_of_year_ignored_without_yearly():
    """年次を使わないなら週番号は 0 に落ちる"""
    ltr = backup_retention_config(week_of_year_for_yearly=26)["long_term_retention"]
    assert ltr["weekOfYear"] == 0


def test_geo_redundant_can_be_disabled():
    """地理冗長は切れる"""
    cfg = backup_retention_config(geo_redundant=False)
    assert cfg["backup"]["geoRedundantBackup"] == "Disabled"


def test_weekly_must_exceed_automatic_retention():
    """週次の長期保持が自動バックアップより短いと ValueError"""
    with pytest.raises(ValueError, match="長くする"):
        backup_retention_config(retention_days=35, weekly_retention_weeks=5)
    assert backup_retention_config(retention_days=35, weekly_retention_weeks=6)


def test_range_checks():
    """保持日数と長期保持と週番号の範囲外は ValueError"""
    for kwargs in (
        {"retention_days": 6},
        {"retention_days": 36},
        {"weekly_retention_weeks": 521},
        {"monthly_retention_months": 121},
        {"yearly_retention_years": 11},
        {"week_of_year_for_yearly": 0},
        {"week_of_year_for_yearly": 53},
    ):
        with pytest.raises(ValueError):
            backup_retention_config(**kwargs)


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = backup_retention_config()
    assert a == backup_retention_config()
    assert json.loads(json.dumps(a)) == a
