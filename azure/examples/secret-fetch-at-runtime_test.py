"""カード secret-fetch-at-runtime の Contract を検証するテスト"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("secret-fetch-at-runtime.py")
    spec = importlib.util.spec_from_file_location("secret_fetch_at_runtime", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load()
key_vault_reference = _mod.key_vault_reference
runtime_secret_config = _mod.runtime_secret_config

PRINCIPAL = "11111111-2222-3333-4444-555555555555"
VERSION = "0123456789abcdef0123456789abcdef"


def _cfg(**kw):
    return runtime_secret_config(
        "example-kv",
        {"DB_PASSWORD": "db-password"},
        PRINCIPAL,
        subscription_id="00000000-0000-0000-0000-000000000000",
        resource_group="example-rg",
        **kw,
    )


def test_reference_format():
    """参照はアプリ設定にそのまま書ける形式"""
    assert key_vault_reference("example-kv", "db-password") == (
        "@Microsoft.KeyVault(SecretUri=https://example-kv.vault.azure.net/secrets/db-password)"
    )


def test_reference_with_version():
    """バージョンを渡すとその版に固定される"""
    assert key_vault_reference("example-kv", "db-password", VERSION).endswith(f"/{VERSION})")


def test_reference_rejects_bad_names():
    """名前とバージョンの形式違いは ValueError"""
    with pytest.raises(ValueError):
        key_vault_reference("Example_KV", "db-password")
    with pytest.raises(ValueError):
        key_vault_reference("example-kv", "db password")
    with pytest.raises(ValueError):
        key_vault_reference("example-kv", "db-password", "v1")


def test_app_settings_sorted_and_referenced():
    """アプリ設定は環境変数名順で、値は参照だけ。秘密そのものは入らない"""
    cfg = runtime_secret_config(
        "example-kv",
        {"B_TOKEN": "b-token", "A_KEY": "a-key"},
        PRINCIPAL,
        subscription_id="00000000-0000-0000-0000-000000000000",
        resource_group="example-rg",
    )
    assert [s["name"] for s in cfg["app_settings"]] == ["A_KEY", "B_TOKEN"]
    assert all(s["value"].startswith("@Microsoft.KeyVault(") for s in cfg["app_settings"])


def test_role_assignment_is_secrets_user():
    """割り当てるのは読み取りだけの Key Vault Secrets User"""
    assignment = _cfg()["role_assignment"]
    assert assignment["scope"].endswith("/vaults/example-kv")
    assert assignment["parameters"]["properties"]["roleDefinitionId"] == (
        "/subscriptions/00000000-0000-0000-0000-000000000000"
        "/providers/Microsoft.Authorization/roleDefinitions/"
        "4633458b-17de-408a-b874-0445c86b69e6"
    )
    assert assignment["role_assignment_name"] == _cfg()["role_assignment"]["role_assignment_name"]


def test_pin_versions_must_match_secrets():
    """secrets に無い環境変数のバージョンは固定できない"""
    with pytest.raises(ValueError, match="secrets に無い"):
        _cfg(pin_versions={"OTHER": VERSION})
    cfg = _cfg(pin_versions={"DB_PASSWORD": VERSION})
    assert cfg["app_settings"][0]["value"].endswith(f"/{VERSION})")


def test_invalid_inputs():
    """空の secrets と GUID でない principal_id は ValueError"""
    with pytest.raises(ValueError):
        runtime_secret_config(
            "example-kv", {}, PRINCIPAL,
            subscription_id="s", resource_group="example-rg",
        )
    with pytest.raises(ValueError):
        runtime_secret_config(
            "example-kv", {"A": "a"}, "not-a-guid",
            subscription_id="s", resource_group="example-rg",
        )


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    secrets = {"DB_PASSWORD": "db-password"}
    before = copy.deepcopy(secrets)
    cfg = runtime_secret_config(
        "example-kv", secrets, PRINCIPAL,
        subscription_id="00000000-0000-0000-0000-000000000000",
        resource_group="example-rg",
    )
    assert secrets == before
    assert json.loads(json.dumps(cfg)) == cfg
