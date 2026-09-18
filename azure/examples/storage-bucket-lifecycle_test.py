"""カード storage-bucket-lifecycle の Contract を検証するテスト"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("storage-bucket-lifecycle.py")
    spec = importlib.util.spec_from_file_location("storage_bucket_lifecycle", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


lifecycle_policy = _load().lifecycle_policy


def _rule(**kwargs):
    return lifecycle_policy("archive-old", **kwargs)["policy"]["rules"][0]


def test_single_enabled_rule():
    """ルールは 1 本で、常に有効・種別は Lifecycle"""
    rule = _rule()
    assert rule["enabled"] is True
    assert rule["name"] == "archive-old"
    assert rule["type"] == "Lifecycle"


def test_blob_types_and_prefix():
    """対象はブロック Blob。プレフィックスは省略すると全体"""
    assert _rule()["definition"]["filters"] == {"blobTypes": ["blockBlob"], "prefixMatch": []}
    filters = _rule(prefix_match=["logs/"])["definition"]["filters"]
    assert filters["prefixMatch"] == ["logs/"]


def test_default_stages():
    """既定はクール 30 日・アーカイブ 90 日・削除 365 日"""
    base = _rule()["definition"]["actions"]["baseBlob"]
    assert base["tierToCool"] == {"daysAfterModificationGreaterThan": 30}
    assert base["tierToArchive"] == {"daysAfterModificationGreaterThan": 90}
    assert base["delete"] == {"daysAfterModificationGreaterThan": 365}


def test_versions_and_snapshots_use_creation_time():
    """旧版とスナップショットは最終更新ではなく作成からの日数で消す"""
    actions = _rule()["definition"]["actions"]
    assert actions["version"]["delete"] == {"daysAfterCreationGreaterThan": 90}
    assert actions["snapshot"]["delete"] == {"daysAfterCreationGreaterThan": 90}


def test_stage_can_be_skipped():
    """None を渡した段階はルールに入らない"""
    actions = _rule(days_to_archive=None, days_to_delete=None)["definition"]["actions"]
    assert "tierToArchive" not in actions["baseBlob"]
    assert "delete" not in actions["baseBlob"]
    actions = _rule(delete_old_versions_after_days=None)["definition"]["actions"]
    assert "version" not in actions


def test_stage_order_enforced():
    """クール → アーカイブ → 削除の順序が逆転すると ValueError"""
    with pytest.raises(ValueError, match="より小さくする"):
        _rule(days_to_cool=90, days_to_archive=30)
    with pytest.raises(ValueError, match="より小さくする"):
        _rule(days_to_archive=400, days_to_delete=365)
    # 途中を飛ばしても残りの順序は検査される
    with pytest.raises(ValueError, match="より小さくする"):
        _rule(days_to_archive=None, days_to_cool=400, days_to_delete=365)


def test_invalid_inputs():
    """空のルール名、0 日以下、何も指定しない場合は ValueError"""
    with pytest.raises(ValueError):
        lifecycle_policy("")
    with pytest.raises(ValueError):
        _rule(days_to_cool=0)
    with pytest.raises(ValueError, match="移行も削除も"):
        _rule(
            days_to_cool=None,
            days_to_archive=None,
            days_to_delete=None,
            delete_old_versions_after_days=None,
            delete_snapshots_after_days=None,
        )


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    prefixes = ["logs/"]
    before = copy.deepcopy(prefixes)
    policy = lifecycle_policy("archive-old", prefix_match=prefixes)
    assert prefixes == before
    assert json.loads(json.dumps(policy)) == policy
