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

SCOPE = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
READ_BLOB = "Microsoft.Storage/storageAccounts/blobServices/containers/read"


def test_permissions_block():
    """permissions は 1 ブロックで、4 つのキーがすべて list になる"""
    cfg = least_privilege_role("Blob Lister", "コンテナ一覧だけ", [READ_BLOB], [SCOPE])
    perms = cfg["role_definition"]["permissions"]
    assert len(perms) == 1
    assert perms[0] == {
        "actions": [READ_BLOB],
        "notActions": [],
        "dataActions": [],
        "notDataActions": [],
    }
    assert cfg["role_definition"]["type"] == "CustomRole"
    assert cfg["role_definition"]["assignableScopes"] == [SCOPE]


def test_data_actions_only():
    """管理プレーンの actions が空でも、データプレーンだけのロールは作れる"""
    data = "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"
    cfg = least_privilege_role("Blob Reader", "Blob 読み取り", [], [SCOPE], data_actions=[data])
    perms = cfg["role_definition"]["permissions"][0]
    assert perms["actions"] == []
    assert perms["dataActions"] == [data]


def test_role_definition_id_is_deterministic():
    """同じ名前とスコープなら定義 ID も同じ（作り直しても重複しない）"""
    a = least_privilege_role("Blob Lister", "説明", [READ_BLOB], [SCOPE])
    b = least_privilege_role("Blob Lister", "別の説明", [READ_BLOB], [SCOPE])
    c = least_privilege_role("Other Role", "説明", [READ_BLOB], [SCOPE])
    assert a["role_definition_id"] == b["role_definition_id"]
    assert a["role_definition_id"] != c["role_definition_id"]


def test_not_actions_narrows_actions():
    """not_actions は actions から除外される操作として別キーに入る"""
    cfg = least_privilege_role(
        "Storage Ops",
        "削除以外",
        ["Microsoft.Storage/storageAccounts/read", "Microsoft.Storage/storageAccounts/write"],
        [SCOPE],
        not_actions=["Microsoft.Storage/storageAccounts/delete"],
    )
    perms = cfg["role_definition"]["permissions"][0]
    assert perms["notActions"] == ["Microsoft.Storage/storageAccounts/delete"]


def test_wildcards_rejected():
    """`*` とプロバイダ丸ごとのワイルドカードは弾く"""
    with pytest.raises(ValueError, match="ワイルドカード"):
        least_privilege_role("All", "全部", ["*"], [SCOPE])
    with pytest.raises(ValueError, match="ワイルドカード"):
        least_privilege_role("Storage All", "全部", ["Microsoft.Storage/*"], [SCOPE])
    # リソース種別まで絞ったワイルドカードは通す
    cfg = least_privilege_role(
        "Account Read", "アカウント読み取り", ["Microsoft.Storage/storageAccounts/*/read"], [SCOPE]
    )
    assert cfg["role_definition"]["permissions"][0]["actions"] == [
        "Microsoft.Storage/storageAccounts/*/read"
    ]


def test_overlap_rejected():
    """actions と not_actions に同じ操作があると ValueError"""
    with pytest.raises(ValueError, match="重複"):
        least_privilege_role("Dup", "説明", [READ_BLOB], [SCOPE], not_actions=[READ_BLOB])


def test_empty_inputs_rejected():
    """操作もスコープも空では作れない"""
    with pytest.raises(ValueError):
        least_privilege_role("Empty", "説明", [], [SCOPE])
    with pytest.raises(ValueError):
        least_privilege_role("NoScope", "説明", [READ_BLOB], [])
    with pytest.raises(ValueError):
        least_privilege_role("BadScope", "説明", [READ_BLOB], ["example-rg"])


def test_multiple_management_groups_rejected():
    """カスタムロールに指定できる管理グループは 1 件まで"""
    mg1 = "/providers/Microsoft.Management/managementGroups/mg-a"
    mg2 = "/providers/Microsoft.Management/managementGroups/mg-b"
    assert least_privilege_role("R", "説明", [READ_BLOB], [mg1])
    with pytest.raises(ValueError, match="管理グループは 1 件"):
        least_privilege_role("R", "説明", [READ_BLOB], [mg1, mg2])


def test_data_actions_cannot_use_management_group():
    """データプレーンの操作を持つロールは管理グループに割り当てられない"""
    mg = "/providers/Microsoft.Management/managementGroups/mg-a"
    data = "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"
    with pytest.raises(ValueError, match="管理グループ"):
        least_privilege_role("R", "説明", [READ_BLOB], [mg], data_actions=[data])


def test_role_writing_actions_rejected():
    """ロールや割り当てを書き換えられる操作は最小権限のロールに入れない"""
    for action in (
        "Microsoft.Authorization/roleAssignments/write",
        "Microsoft.Authorization/roleDefinitions/write",
        "Microsoft.Authorization/elevateAccess/action",
        # ワイルドカードで包んでも同じ
        "Microsoft.Authorization/roleAssignments/*",
    ):
        with pytest.raises(ValueError, match="ロールを書き換えられる"):
            least_privilege_role("R", "説明", [action], [SCOPE])
    # 読み取りは通す
    assert least_privilege_role(
        "R", "説明", ["Microsoft.Authorization/roleAssignments/read"], [SCOPE]
    )


def test_pure_and_serializable():
    """引数のリストを変更せず、返り値は JSON にできる"""
    actions = [READ_BLOB]
    before = copy.deepcopy(actions)
    cfg = least_privilege_role("Blob Lister", "説明", actions, [SCOPE])
    cfg["role_definition"]["permissions"][0]["actions"].append("mutated")
    assert actions == before
    assert json.loads(json.dumps(cfg)) == cfg
