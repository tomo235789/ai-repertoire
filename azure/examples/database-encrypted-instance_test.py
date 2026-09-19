"""カード database-encrypted-instance の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("database-encrypted-instance.py")
    spec = importlib.util.spec_from_file_location("database_encrypted_instance", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


encrypted_server_config = _load().encrypted_server_config

SUBNET = (
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
    "/providers/Microsoft.Network/virtualNetworks/example-vnet/subnets/db"
)
ZONE = (
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
    "/providers/Microsoft.Network/privateDnsZones/example.postgres.database.azure.com"
)
KEY = "https://example-kv.vault.azure.net/keys/data-key/0123456789abcdef0123456789abcdef"
UAMI = (
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
    "/providers/Microsoft.ManagedIdentity/userAssignedIdentities/example-mi"
)


def _cfg(**kw):
    return encrypted_server_config("example-db", "japaneast", "appadmin", **kw)


def test_password_auth_disabled():
    """パスワード認証は使わず Entra ID だけ"""
    auth = _cfg()["properties"]["authConfig"]
    assert auth == {"activeDirectoryAuth": "Enabled", "passwordAuth": "Disabled"}


def test_public_access_disabled_by_default():
    """公衆ネットワークからの接続は既定で塞ぐ"""
    assert _cfg()["properties"]["network"]["publicNetworkAccess"] == "Disabled"


def test_system_managed_encryption_by_default():
    """鍵を渡さなければ Microsoft 管理鍵で、ID も付かない"""
    cfg = _cfg()
    assert cfg["properties"]["dataEncryption"] == {"type": "SystemManaged"}
    assert cfg["identity"] == {"type": "None"}


def test_customer_managed_key():
    """顧客管理鍵にはユーザー割り当て ID が付く"""
    cfg = _cfg(key_vault_key_uri=KEY, user_assigned_identity_id=UAMI)
    enc = cfg["properties"]["dataEncryption"]
    assert enc["type"] == "AzureKeyVault"
    assert enc["primaryKeyUri"] == KEY
    assert cfg["identity"] == {"type": "UserAssigned", "userAssignedIdentities": {UAMI: {}}}


def test_private_networking():
    """サブネットとゾーンを渡すと閉域構成になる"""
    net = _cfg(delegated_subnet_id=SUBNET, private_dns_zone_id=ZONE)["properties"]["network"]
    assert net["delegatedSubnetResourceId"] == SUBNET
    assert net["privateDnsZoneArmResourceId"] == ZONE
    assert net["publicNetworkAccess"] == "Disabled"


def test_paired_arguments_required():
    """閉域構成も顧客管理鍵も片方だけでは指定できない"""
    with pytest.raises(ValueError, match="閉域構成"):
        _cfg(delegated_subnet_id=SUBNET)
    with pytest.raises(ValueError, match="顧客管理鍵"):
        _cfg(key_vault_key_uri=KEY)


def test_high_availability_default():
    """既定はゾーン冗長"""
    assert _cfg()["properties"]["highAvailability"] == {"mode": "ZoneRedundant"}
    with pytest.raises(ValueError):
        _cfg(high_availability="Always")


def test_invalid_inputs():
    """名前・ログイン名・ストレージの不正は ValueError"""
    with pytest.raises(ValueError):
        encrypted_server_config("Example_DB", "japaneast", "appadmin")
    with pytest.raises(ValueError):
        encrypted_server_config("example-db", "japaneast", "postgres")
    with pytest.raises(ValueError):
        encrypted_server_config("example-db", "japaneast", "1admin")
    with pytest.raises(ValueError):
        _cfg(storage_gb=16)


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    assert _cfg() == _cfg()
    cfg = _cfg()
    assert json.loads(json.dumps(cfg)) == cfg
