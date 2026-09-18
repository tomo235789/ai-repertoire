"""カード iam-read-only-policy の Contract を検証するテスト"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("iam-read-only-policy.py")
    spec = importlib.util.spec_from_file_location("iam_read_only_policy", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load()
read_only_role = _mod.read_only_role
built_in_reader_role_id = _mod.built_in_reader_role_id
SECRET_REVEALING_ACTIONS = _mod.SECRET_REVEALING_ACTIONS

SCOPE = "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"


def test_actions_are_read_only():
    """許可するのはプロバイダごとの `/*/read` だけ"""
    cfg = read_only_role("Storage Reader", ["Microsoft.Storage"], [SCOPE])
    perms = cfg["role_definition"]["permissions"][0]
    assert perms["actions"] == ["Microsoft.Storage/*/read"]
    assert perms["dataActions"] == []


def test_providers_are_sorted():
    """プロバイダの並び順が違っても同じ定義になる"""
    a = read_only_role("R", ["Microsoft.Web", "Microsoft.Storage"], [SCOPE])
    b = read_only_role("R", ["Microsoft.Storage", "Microsoft.Web"], [SCOPE])
    assert a == b
    assert a["role_definition"]["permissions"][0]["actions"] == [
        "Microsoft.Storage/*/read",
        "Microsoft.Web/*/read",
    ]


def test_secret_revealing_actions_excluded():
    """鍵と秘密の読み取りは not_actions で必ず外す"""
    cfg = read_only_role("KV Reader", ["Microsoft.KeyVault"], [SCOPE])
    assert cfg["role_definition"]["permissions"][0]["notActions"] == list(
        SECRET_REVEALING_ACTIONS
    )


def test_data_read_actions_are_opt_in():
    """データプレーンの読み取りは明示したときだけ入る"""
    action = "Microsoft.Storage/storageAccounts/blobServices/containers/blobs/read"
    cfg = read_only_role("Blob Reader", ["Microsoft.Storage"], [SCOPE], data_read_actions=[action])
    assert cfg["role_definition"]["permissions"][0]["dataActions"] == [action]


def test_write_action_rejected_in_data_actions():
    """データプレーンにも書き込みは混ぜられない"""
    with pytest.raises(ValueError, match="読み取り以外"):
        read_only_role(
            "Bad",
            ["Microsoft.Storage"],
            [SCOPE],
            data_read_actions=["Microsoft.Storage/storageAccounts/blobServices/containers/blobs/write"],
        )


def test_role_definition_id_is_deterministic():
    """同じ名前とスコープなら定義 ID も同じ"""
    a = read_only_role("Storage Reader", ["Microsoft.Storage"], [SCOPE])
    b = read_only_role("Storage Reader", ["Microsoft.Storage"], [SCOPE], description="別")
    assert a["role_definition_id"] == b["role_definition_id"]


def test_built_in_reader_role_id():
    """組み込み Reader の定義 ID はサブスクリプション配下になる"""
    assert built_in_reader_role_id(SCOPE) == (
        "/subscriptions/00000000-0000-0000-0000-000000000000"
        "/providers/Microsoft.Authorization/roleDefinitions/"
        "acdd72a7-3385-48ef-bd42-f606fba81ae7"
    )
    with pytest.raises(ValueError):
        built_in_reader_role_id("example-rg")


def test_invalid_inputs():
    """空の入力と形式違いは ValueError"""
    with pytest.raises(ValueError):
        read_only_role("R", [], [SCOPE])
    with pytest.raises(ValueError):
        read_only_role("R", ["Microsoft.Storage"], [])
    with pytest.raises(ValueError):
        read_only_role("R", ["storage"], [SCOPE])


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    providers = ["Microsoft.Storage"]
    before = copy.deepcopy(providers)
    cfg = read_only_role("R", providers, [SCOPE])
    assert providers == before
    assert json.loads(json.dumps(cfg)) == cfg
