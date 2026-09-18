"""カード storage-bucket-private の Contract を検証するテスト"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("storage-bucket-private.py")
    spec = importlib.util.spec_from_file_location("storage_bucket_private", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


private_container_config = _load().private_container_config

BASE = dict(
    subscription_id="00000000-0000-0000-0000-000000000000",
    resource_group="example-rg",
)
UAMI = (
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
    "/providers/Microsoft.ManagedIdentity/userAssignedIdentities/example-mi"
)


def _cfg(**kw):
    return private_container_config(
        "examplestorage", "private-data", "japaneast", **{**BASE, **kw}
    )


def test_public_access_is_blocked():
    """公開アクセスはアカウント・ネットワーク・コンテナの三箇所で塞ぐ"""
    props = _cfg()["account"]["properties"]
    assert props["allowBlobPublicAccess"] is False
    assert props["publicNetworkAccess"] == "Disabled"
    assert props["networkAcls"]["defaultAction"] == "Deny"
    assert _cfg()["container"]["blob_container"]["properties"]["publicAccess"] == "None"


def test_shared_key_disabled_and_tls_enforced():
    """共有キー認証を止め、TLS 1.2 以上と HTTPS のみを強制する"""
    props = _cfg()["account"]["properties"]
    assert props["allowSharedKeyAccess"] is False
    assert props["minimumTlsVersion"] == "TLS1_2"
    assert props["supportsHttpsTrafficOnly"] is True


def test_encryption_defaults_to_microsoft_key():
    """鍵を渡さなければ Microsoft 管理鍵。インフラ二重暗号化は常に有効"""
    enc = _cfg()["account"]["properties"]["encryption"]
    assert enc["keySource"] == "Microsoft.Storage"
    assert enc["requireInfrastructureEncryption"] is True
    assert "keyvaultproperties" not in enc


def test_customer_managed_key():
    """顧客管理鍵は金庫の URI・鍵名・版に分け、ユーザー割り当て ID で読む"""
    uri = "https://example-kv.vault.azure.net/keys/data/abcdef"
    cfg = _cfg(key_vault_key_uri=uri, encryption_identity_id=UAMI)
    enc = cfg["account"]["properties"]["encryption"]
    assert enc["keySource"] == "Microsoft.Keyvault"
    assert enc["keyvaultproperties"] == {
        "keyvaulturi": "https://example-kv.vault.azure.net",
        "keyname": "data",
        "keyversion": "abcdef",
    }
    assert enc["identity"] == {"userAssignedIdentity": UAMI}
    assert cfg["account"]["identity"] == {
        "type": "UserAssigned",
        "userAssignedIdentities": {UAMI: {}},
    }


def test_customer_managed_key_needs_user_assigned_identity():
    """作成と同時の顧客管理鍵にはユーザー割り当て ID が要る"""
    uri = "https://example-kv.vault.azure.net/keys/data/abcdef"
    with pytest.raises(ValueError, match="ユーザー割り当て ID"):
        _cfg(key_vault_key_uri=uri)
    with pytest.raises(ValueError, match="ユーザー割り当て ID"):
        _cfg(key_vault_key_uri=uri, encryption_identity_id="example-mi")


def test_key_uri_without_version():
    """版を省いた URI なら keyversion は空文字（最新を追う）"""
    enc = _cfg(
        key_vault_key_uri="https://example-kv.vault.azure.net/keys/data",
        encryption_identity_id=UAMI,
    )["account"]["properties"]["encryption"]
    assert enc["keyvaultproperties"]["keyversion"] == ""


def test_key_uri_format_checked():
    """鍵の URI の形式違いは ValueError"""
    with pytest.raises(ValueError, match="鍵の URI"):
        _cfg(
            key_vault_key_uri="https://example-kv.vault.azure.net/secrets/data",
            encryption_identity_id=UAMI,
        )


def test_ip_rules_open_public_network():
    """許可 IP を渡したときだけ公衆ネットワークを開き、既定動作は Deny のまま"""
    cfg = _cfg(allowed_ip_rules=["203.0.113.10"])
    props = cfg["account"]["properties"]
    assert props["publicNetworkAccess"] == "Enabled"
    assert props["networkAcls"]["defaultAction"] == "Deny"
    assert props["networkAcls"]["ipRules"] == [
        {"value": "203.0.113.10", "action": "Allow"}
    ]


def test_reader_role_assignments():
    """読み取り許可は Storage Blob Data Reader をコンテナのスコープで割り当てる"""
    cfg = _cfg(reader_principal_ids=["11111111-2222-3333-4444-555555555555"])
    (assignment,) = cfg["role_assignments"]
    assert assignment["scope"].endswith("/containers/private-data")
    assert assignment["parameters"]["properties"]["roleDefinitionId"] == (
        "/subscriptions/00000000-0000-0000-0000-000000000000"
        "/providers/Microsoft.Authorization/roleDefinitions/"
        "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1"
    )
    assert assignment["role_assignment_name"] == _cfg(
        reader_principal_ids=["11111111-2222-3333-4444-555555555555"]
    )["role_assignments"][0]["role_assignment_name"]


def test_principal_type_can_be_changed():
    """人やグループにも割り当てられる"""
    cfg = _cfg(
        reader_principal_ids=["11111111-2222-3333-4444-555555555555"],
        reader_principal_type="Group",
    )
    assert cfg["role_assignments"][0]["parameters"]["properties"]["principalType"] == "Group"
    with pytest.raises(ValueError, match="プリンシパル種別"):
        _cfg(reader_principal_type="Everyone")


def test_anonymous_principal_rejected():
    """匿名・全員に相当するプリンシパルは弾く"""
    with pytest.raises(ValueError):
        _cfg(reader_principal_ids=["allUsers"])
    with pytest.raises(ValueError):
        _cfg(reader_principal_ids=["allAuthenticatedUsers"])


def test_invalid_names():
    """アカウント名とコンテナ名の形式違いは ValueError"""
    with pytest.raises(ValueError):
        private_container_config("ExampleStorage", "private-data", "japaneast", **BASE)
    with pytest.raises(ValueError):
        private_container_config("examplestorage", "Private_Data", "japaneast", **BASE)


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    tags = {"env": "prod"}
    before = copy.deepcopy(tags)
    cfg = _cfg(tags=tags)
    assert tags == before
    assert cfg["account"]["tags"] == {"env": "prod"}
    assert json.loads(json.dumps(cfg)) == cfg
