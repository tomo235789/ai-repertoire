"""カード iam-least-privilege-role の Contract を検証するテスト"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("iam-least-privilege-role.py")
    spec = importlib.util.spec_from_file_location("iam_least_privilege_role", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


least_privilege_role = _load().least_privilege_role

GET = "storage.objects.get"
LIST = "storage.objects.list"


def test_permissions_sorted_and_deduplicated():
    """権限は重複を除いて名前順に並ぶ"""
    role = least_privilege_role("objectLister", "Object Lister", [LIST, GET, GET])["role"]
    assert role["includedPermissions"] == [GET, LIST]


def test_default_stage_is_ga():
    """既定の公開ステージは GA"""
    assert least_privilege_role("objectLister", "Object Lister", [GET])["role"]["stage"] == "GA"


def test_role_id_is_returned_separately():
    """ロール ID は Role の外に返る（create の roleId に渡す）"""
    cfg = least_privilege_role("objectLister", "Object Lister", [GET])
    assert cfg["role_id"] == "objectLister"
    assert "role_id" not in cfg["role"]


def test_wildcard_rejected():
    """権限にワイルドカードは使えない"""
    with pytest.raises(ValueError, match="ワイルドカード"):
        least_privilege_role("objectLister", "Object Lister", ["storage.objects.*"])


def test_privilege_escalation_rejected():
    """権限昇格につながる権限は明示許可が要る"""
    with pytest.raises(ValueError, match="権限昇格"):
        least_privilege_role("objectLister", "Object Lister", [GET, "resourcemanager.projects.setIamPolicy"])
    cfg = least_privilege_role(
        "objectLister", "Object Lister", [GET, "iam.serviceAccounts.actAs"],
        allow_privilege_escalation=True,
    )
    assert "iam.serviceAccounts.actAs" in cfg["role"]["includedPermissions"]


def test_set_iam_policy_permissions_rejected():
    """setIamPolicy で終わる権限はどのリソースでも権限昇格になる"""
    for permission in (
        "resourcemanager.folders.setIamPolicy",
        "resourcemanager.organizations.setIamPolicy",
        "iam.serviceAccounts.setIamPolicy",
    ):
        with pytest.raises(ValueError, match="権限昇格"):
            least_privilege_role("objectLister", "Object Lister", [permission])
    with pytest.raises(ValueError, match="権限昇格"):
        least_privilege_role("objectLister", "Object Lister", ["iam.serviceAccounts.signJwt"])


def test_permission_format():
    """<サービス>.<リソース>.<動詞> の形でないと ValueError"""
    with pytest.raises(ValueError, match="権限の形式"):
        least_privilege_role("objectLister", "Object Lister", ["storage.get"])
    with pytest.raises(ValueError, match="権限の形式"):
        least_privilege_role("objectLister", "Object Lister", ["Storage.Objects.Get"])


def test_invalid_inputs():
    """ロール ID・タイトル・権限・ステージの不正は ValueError"""
    with pytest.raises(ValueError):
        least_privilege_role("a", "R", [GET])
    with pytest.raises(ValueError):
        least_privilege_role("objectLister", "", [GET])
    with pytest.raises(ValueError):
        least_privilege_role("objectLister", "R", [])
    with pytest.raises(ValueError):
        least_privilege_role("objectLister", "R", [GET], stage="PREVIEW")


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    permissions = [LIST, GET]
    before = copy.deepcopy(permissions)
    cfg = least_privilege_role("objectLister", "Object Lister", permissions)
    assert permissions == before
    assert json.loads(json.dumps(cfg)) == cfg
