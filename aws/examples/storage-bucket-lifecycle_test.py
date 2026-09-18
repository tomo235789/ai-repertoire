"""カード storage-bucket-lifecycle の Contract を検証するテスト"""

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


lifecycle_rules = _load().lifecycle_rules


def test_snapshot_all_actions():
    """4 つの日数をすべて渡すと 1 ルールに 4 つのアクションが並ぶ"""
    cfg = lifecycle_rules(30, 365, 90, 7, prefix="logs/")
    assert cfg == {
        "Rules": [
            {
                "ID": "lifecycle-logs/",
                "Filter": {"Prefix": "logs/"},
                "Status": "Enabled",
                "Transitions": [{"Days": 30, "StorageClass": "STANDARD_IA"}],
                "Expiration": {"Days": 365},
                "NoncurrentVersionExpiration": {"NoncurrentDays": 90},
                "AbortIncompleteMultipartUpload": {"DaysAfterInitiation": 7},
            }
        ]
    }
    json.dumps(cfg)


def test_empty_prefix_targets_all_objects():
    """prefix 省略時は Filter.Prefix が "" で ID は "lifecycle" """
    rule = lifecycle_rules(30, 365, 90, 7)["Rules"][0]
    assert rule["Filter"] == {"Prefix": ""}
    assert rule["ID"] == "lifecycle"


def test_none_omits_action():
    """None を渡したアクションはルールに含まれない"""
    rule = lifecycle_rules(None, 30, None, None)["Rules"][0]
    assert rule == {"ID": "lifecycle", "Filter": {"Prefix": ""}, "Status": "Enabled", "Expiration": {"Days": 30}}
    rule = lifecycle_rules(None, None, None, 7)["Rules"][0]
    assert "Expiration" not in rule and rule["AbortIncompleteMultipartUpload"] == {"DaysAfterInitiation": 7}


def test_storage_class_selectable():
    """storage_class で移行先を変えられる。GLACIER 系は 30 日未満でも可"""
    rule = lifecycle_rules(1, 10, None, None, storage_class="DEEP_ARCHIVE")["Rules"][0]
    assert rule["Transitions"] == [{"Days": 1, "StorageClass": "DEEP_ARCHIVE"}]


def test_transition_must_precede_expiration():
    """transition_days >= expiration_days は ValueError"""
    with pytest.raises(ValueError):
        lifecycle_rules(365, 365, None, None)
    with pytest.raises(ValueError):
        lifecycle_rules(400, 365, None, None)


def test_ia_requires_30_days():
    """STANDARD_IA / ONEZONE_IA への移行は 30 日以上"""
    with pytest.raises(ValueError):
        lifecycle_rules(29, 365, None, None)
    with pytest.raises(ValueError):
        lifecycle_rules(29, 365, None, None, storage_class="ONEZONE_IA")
    assert lifecycle_rules(30, 365, None, None)["Rules"][0]["Transitions"][0]["Days"] == 30


@pytest.mark.parametrize("args", [(0, 365, 90, 7), (30, -1, 90, 7), (30, 365, 0, 7), (30, 365, 90, 0), (30.5, 365, 90, 7), (True, 365, 90, 7)])
def test_non_positive_or_non_int_days_raise(args):
    """日数は 1 以上の int。0・負数・小数・bool は ValueError"""
    with pytest.raises(ValueError):
        lifecycle_rules(*args)


def test_no_action_or_bad_storage_class_raises():
    """アクションが 1 つも無い、または未知のストレージクラスは ValueError"""
    with pytest.raises(ValueError):
        lifecycle_rules(None, None, None, None)
    with pytest.raises(ValueError):
        lifecycle_rules(30, 365, None, None, storage_class="REDUCED_REDUNDANCY")


def test_deterministic():
    """同じ入力に同じ出力"""
    assert lifecycle_rules(30, 365, 90, 7) == lifecycle_rules(30, 365, 90, 7)
