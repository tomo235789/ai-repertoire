"""カード storage-object-versioning の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("storage-object-versioning.py")
    spec = importlib.util.spec_from_file_location("storage_object_versioning", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


versioning_config = _load().versioning_config


def test_versioning_and_soft_delete_enabled():
    """バージョン管理と論理削除は常に有効で、完全削除は許さない"""
    cfg = versioning_config()
    assert cfg["isVersioningEnabled"] is True
    assert cfg["deleteRetentionPolicy"] == {
        "enabled": True,
        "days": 30,
        "allowPermanentDelete": False,
    }
    assert cfg["containerDeleteRetentionPolicy"] == {"enabled": True, "days": 30}


def test_change_feed_always_enabled():
    """変更フィードは常に有効。ポイントインタイム復元の前提になる"""
    assert versioning_config()["changeFeed"] == {"enabled": True}


def test_restore_policy_disabled_by_default():
    """復元は既定では無効"""
    assert versioning_config()["restorePolicy"] == {"enabled": False}


def test_restore_policy_enabled():
    """復元日数を渡すと有効になる"""
    cfg = versioning_config(point_in_time_restore_days=7)
    assert cfg["restorePolicy"] == {"enabled": True, "days": 7}


def test_restore_days_must_be_shorter_than_retention():
    """復元日数は論理削除の保持日数より短くする"""
    with pytest.raises(ValueError, match="blob_retention_days より小さく"):
        versioning_config(blob_retention_days=7, point_in_time_restore_days=7)
    with pytest.raises(ValueError):
        versioning_config(point_in_time_restore_days=0)


def test_retention_days_range():
    """保持日数は 1〜365 日"""
    for kwargs in ({"blob_retention_days": 0}, {"blob_retention_days": 366},
                   {"container_retention_days": 0}, {"container_retention_days": 366}):
        with pytest.raises(ValueError):
            versioning_config(**kwargs)
    assert versioning_config(blob_retention_days=365)["deleteRetentionPolicy"]["days"] == 365


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    assert versioning_config(point_in_time_restore_days=7) == versioning_config(
        point_in_time_restore_days=7
    )
    cfg = versioning_config()
    assert json.loads(json.dumps(cfg)) == cfg
