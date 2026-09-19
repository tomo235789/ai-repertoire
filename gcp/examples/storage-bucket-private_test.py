"""storage-bucket-private（GCP）の Contract を検証する。"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

_spec = importlib.util.spec_from_file_location("_mod", Path(__file__).with_name("storage-bucket-private.py"))
assert _spec and _spec.loader
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
private_bucket_config = _mod.private_bucket_config

PROJECT = "my-project"
KMS = "projects/my-project/locations/asia-northeast1/keyRings/ring/cryptoKeys/key"
SA = "serviceAccount:app@my-project.iam.gserviceaccount.com"


def build(**kwargs: Any) -> dict[str, Any]:
    params = {"name": "example-bucket", "location": "asia-northeast1", "project": PROJECT}
    params.update(kwargs)
    return private_bucket_config(**params)


def test_public_access_is_prevented_and_acl_is_disabled() -> None:
    """公開アクセスは enforced で禁止し、均一バケットレベルアクセスで ACL を無効にする。"""
    iam = build()["bucket"]["iamConfiguration"]
    assert iam["publicAccessPrevention"] == "enforced"
    assert iam["uniformBucketLevelAccess"]["enabled"] is True


def test_versioning_is_enabled_by_default() -> None:
    """既定でバージョニングを有効にする（誤削除から守る）。"""
    assert build()["bucket"]["versioning"] == {"enabled": True}


def test_cmek_is_included_only_when_given() -> None:
    """CMEK を渡したときだけ encryption を含める。渡さなければ Google 管理鍵。"""
    assert "encryption" not in build()["bucket"]
    assert build(kms_key_name=KMS)["bucket"]["encryption"] == {"defaultKmsKeyName": KMS}


def test_reader_members_become_object_viewer_binding() -> None:
    """読み取りメンバーは objectViewer の binding 1 つにまとまり、重複は除かれ順序は保たれる。"""
    policy = build(reader_members=[SA, SA, "group:dev@example.com"])["iam_policy"]
    assert policy["version"] == 3
    assert policy["bindings"] == [{"role": "roles/storage.objectViewer", "members": [SA, "group:dev@example.com"]}]


def test_no_members_means_no_bindings() -> None:
    """メンバーを渡さなければ binding は空（誰にも権限を与えない）。"""
    assert build()["iam_policy"]["bindings"] == []


def test_public_members_are_rejected() -> None:
    """allUsers / allAuthenticatedUsers は ValueError で弾く。"""
    for member in ("allUsers", "allAuthenticatedUsers"):
        with pytest.raises(ValueError, match="公開メンバー"):
            build(reader_members=[member])


def test_invalid_inputs_are_rejected() -> None:
    """名前・プロジェクト・CMEK・保持期間の形式違反は ValueError。"""
    with pytest.raises(ValueError):
        build(name="Example_Bucket")  # 大文字は不可
    with pytest.raises(ValueError):
        build(name="goog-bucket")  # goog を含む名前は不可
    with pytest.raises(ValueError):
        build(project="X")
    with pytest.raises(ValueError):
        build(kms_key_name="projects/p/keys/k")
    with pytest.raises(ValueError):
        build(retention_period_seconds=0)
    with pytest.raises(ValueError):
        build(reader_members=["app@my-project.iam.gserviceaccount.com"])  # 接頭辞が無い


def test_labels_and_retention_are_optional_and_sorted() -> None:
    """labels はキー順に並び、retention_policy は渡したときだけ入る。"""
    out = build(labels={"env": "prod", "app": "api"}, retention_period_seconds=3600)["bucket"]
    assert list(out["labels"]) == ["app", "env"]
    assert out["retentionPolicy"] == {"retentionPeriod": "3600"}


def test_is_pure_and_json_serializable() -> None:
    """同じ入力に同じ出力を返し、入力を変更せず、JSON 化できる。"""
    members = [SA]
    labels = {"env": "prod"}
    first = build(reader_members=members, labels=labels)
    second = build(reader_members=members, labels=labels)
    assert first == second
    assert members == [SA] and labels == {"env": "prod"}
    assert json.loads(json.dumps(first)) == first
