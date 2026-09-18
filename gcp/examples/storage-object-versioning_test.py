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


def test_versioning_enabled():
    """版管理は常に有効"""
    assert versioning_config()["properties"]["versioning"] == {"enabled": True}


def test_soft_delete_in_seconds():
    """論理削除の保持は秒で渡す"""
    policy = versioning_config()["properties"]["softDeletePolicy"]
    assert policy == {"retentionDurationSeconds": 7 * 86400}
    policy = versioning_config(soft_delete_retention_days=90)["properties"]["softDeletePolicy"]
    assert policy == {"retentionDurationSeconds": 90 * 86400}


def test_lifecycle_keeps_newer_versions():
    """旧版の削除は新しい版を残す条件付き"""
    rule = versioning_config(keep_newer_versions=5)["lifecycle_rules"][0]
    assert rule["action"] == {"type": "Delete"}
    assert rule["condition"] == {"daysSinceNoncurrentTime": 30, "numNewerVersions": 5}


def test_retention_policy_is_opt_in():
    """保持ポリシーは渡したときだけ入る"""
    assert "retentionPolicy" not in versioning_config()["properties"]
    props = versioning_config(retention_period_seconds=3600)["properties"]
    assert props["retentionPolicy"] == {"retentionPeriod": 3600}


def test_invalid_inputs():
    """残す版の数・日数・保持期間の不正は ValueError"""
    with pytest.raises(ValueError):
        versioning_config(keep_newer_versions=0)
    with pytest.raises(ValueError):
        versioning_config(delete_noncurrent_after_days=0)
    with pytest.raises(ValueError):
        versioning_config(soft_delete_retention_days=6)
    with pytest.raises(ValueError):
        versioning_config(soft_delete_retention_days=91)
    with pytest.raises(ValueError):
        versioning_config(retention_period_seconds=0)


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = versioning_config()
    assert a == versioning_config()
    assert json.loads(json.dumps(a)) == a
