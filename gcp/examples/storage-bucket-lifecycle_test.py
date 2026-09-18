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


lifecycle_rules = _load().lifecycle_rules


def test_default_rules():
    """既定は NEARLINE 30 日・COLDLINE 90 日・削除 365 日・旧版 30 日"""
    rules = lifecycle_rules()
    assert rules[0] == {
        "action": {"type": "SetStorageClass", "storageClass": "NEARLINE"},
        "condition": {"age": 30},
    }
    assert rules[1]["action"]["storageClass"] == "COLDLINE"
    assert rules[2] == {"action": {"type": "Delete"}, "condition": {"age": 365}}
    # 既定は COLDLINE 90 日 + 最低保存 90 日 = 180 日以降の削除で、365 日はその条件を満たす
    assert rules[3]["condition"]["daysSinceNoncurrentTime"] == 30


def test_transitions_sorted_by_class_order():
    """入力の順序に関係なく、単価が下がる順に並ぶ"""
    rules = lifecycle_rules(
        transitions={"ARCHIVE": 365, "NEARLINE": 30}, delete_after_days=None
    )
    assert [r["action"]["storageClass"] for r in rules[:2]] == ["NEARLINE", "ARCHIVE"]


def test_noncurrent_rule_keeps_newer_versions():
    """旧版の削除は新しい版を指定数だけ残す"""
    condition = lifecycle_rules(keep_newer_versions=5)[-1]["condition"]
    assert condition["numNewerVersions"] == 5


def test_prefix_applies_to_every_rule():
    """プレフィックスはすべての規則に付く"""
    rules = lifecycle_rules(matches_prefix=["logs/"])
    assert all(rule["condition"]["matchesPrefix"] == ["logs/"] for rule in rules)


def test_rules_can_be_omitted():
    """None を渡した削除規則は作られない"""
    rules = lifecycle_rules(delete_after_days=None, delete_noncurrent_after_days=None)
    assert all(rule["action"]["type"] == "SetStorageClass" for rule in rules)


def test_transition_before_minimum_duration_allowed():
    """最低保存期間は移行のタイミングを縛らない。30 日で Coldline に移せる"""
    rules = lifecycle_rules(transitions={"COLDLINE": 30}, delete_after_days=None)
    assert rules[0]["condition"]["age"] == 30


def test_delete_respects_minimum_storage_duration():
    """最後の階層に移してから最低保存期間を置かずに消すと ValueError"""
    with pytest.raises(ValueError, match="最低保存期間"):
        lifecycle_rules(transitions={"ARCHIVE": 30}, delete_after_days=100)
    # 30 日で Archive に移すなら、削除は 395 日以降
    rules = lifecycle_rules(transitions={"ARCHIVE": 30}, delete_after_days=395)
    assert rules[-1]["condition"]["daysSinceNoncurrentTime"] == 30


def test_order_enforced():
    """移行の順序の逆転と、移行より早い削除は ValueError"""
    with pytest.raises(ValueError, match="より早く移行する"):
        lifecycle_rules(transitions={"NEARLINE": 120, "COLDLINE": 90}, delete_after_days=None)
    with pytest.raises(ValueError, match="より後にする"):
        lifecycle_rules(transitions={"NEARLINE": 30}, delete_after_days=30)


def test_minimum_duration_counts_from_creation():
    """最低保存期間は前の階層での経過も算入されるので、作成からの日数で見る"""
    # 30 日で Archive に移し、作成から 365 日で削除するのは有効
    rules = lifecycle_rules(transitions={"ARCHIVE": 30}, delete_after_days=365)
    assert rules[-2]["condition"]["age"] == 365
    with pytest.raises(ValueError, match="最低保存期間"):
        lifecycle_rules(transitions={"ARCHIVE": 30}, delete_after_days=364)


def test_invalid_inputs():
    """未知のクラス、STANDARD への移行、負の値は ValueError"""
    with pytest.raises(ValueError):
        lifecycle_rules(transitions={"GLACIER": 30})
    with pytest.raises(ValueError, match="STANDARD"):
        lifecycle_rules(transitions={"STANDARD": 30})
    with pytest.raises(ValueError):
        lifecycle_rules(keep_newer_versions=-1)
    with pytest.raises(ValueError):
        lifecycle_rules(delete_noncurrent_after_days=0)


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    transitions = {"NEARLINE": 30}
    before = copy.deepcopy(transitions)
    rules = lifecycle_rules(transitions=transitions, delete_after_days=None)
    assert transitions == before
    assert json.loads(json.dumps(rules)) == rules
