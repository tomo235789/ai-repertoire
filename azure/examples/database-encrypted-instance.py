"""カード database-encrypted-instance: 保存時暗号化を有効にした DB の構成を組み立てる純粋関数。

`azure-mgmt-rdbms` の `servers.begin_create`（PostgreSQL フレキシブルサーバー）に
渡す引数を返す。API は呼ばず、資格情報も作らない。
"""

from __future__ import annotations

import re

_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9-]{1,61}[a-z0-9]$")

# 高可用性の指定。ゾーン冗長は対応リージョンでのみ使える
HA_MODES = ("Disabled", "SameZone", "ZoneRedundant")


def encrypted_server_config(
    name: str,
    location: str,
    admin_login: str,
    *,
    version: str = "16",
    sku_name: str = "Standard_D2ds_v5",
    storage_gb: int = 128,
    delegated_subnet_id: str | None = None,
    private_dns_zone_id: str | None = None,
    key_vault_key_uri: str | None = None,
    user_assigned_identity_id: str | None = None,
    high_availability: str = "ZoneRedundant",
) -> dict:
    """保存時暗号化と閉域接続を前提にしたサーバーの構成を返す。

    Args:
        name: サーバー名。英小文字・数字・ハイフンで 3〜63 文字
        location: リージョン
        admin_login: 管理者のログイン名
        version: PostgreSQL のメジャーバージョン
        sku_name: 計算リソースの SKU
        storage_gb: ストレージ容量
        delegated_subnet_id: 委任済みサブネットの ARM ID。渡すと閉域構成になる
        private_dns_zone_id: 閉域構成で使うプライベート DNS ゾーンの ARM ID
        key_vault_key_uri: 顧客管理鍵の URI。省略すると Microsoft 管理鍵
        user_assigned_identity_id: 顧客管理鍵を読むユーザー割り当て ID の ARM ID
        high_availability: HA_MODES のいずれか

    Returns:
        location と properties、identity を持つ dict

    Raises:
        ValueError: 名前やログイン名の形式違い、ストレージが 32 GB 未満、
            未知の高可用性モード、閉域構成や顧客管理鍵の指定が揃っていない場合
    """
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"サーバー名は英小文字・数字・ハイフンで 3〜63 文字: {name!r}")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]{0,62}", admin_login):
        raise ValueError(f"管理者ログイン名の形式が不正: {admin_login!r}")
    if admin_login.lower() in {"azure_superuser", "postgres", "admin", "administrator"}:
        raise ValueError(f"予約済み・推測されやすいログイン名は使わない: {admin_login!r}")
    if storage_gb < 32:
        raise ValueError(f"ストレージは 32 GB 以上: {storage_gb}")
    if high_availability not in HA_MODES:
        raise ValueError(f"高可用性は {HA_MODES} のいずれか: {high_availability!r}")
    if (delegated_subnet_id is None) != (private_dns_zone_id is None):
        raise ValueError("閉域構成にはサブネットとプライベート DNS ゾーンの両方が要る")
    if (key_vault_key_uri is None) != (user_assigned_identity_id is None):
        raise ValueError("顧客管理鍵には鍵の URI とユーザー割り当て ID の両方が要る")

    properties: dict = {
        "version": version,
        "administratorLogin": admin_login,
        # パスワード認証は使わず Entra ID の管理者だけを認める
        "authConfig": {
            "activeDirectoryAuth": "Enabled",
            "passwordAuth": "Disabled",
        },
        "storage": {"storageSizeGB": storage_gb, "autoGrow": "Enabled"},
        "highAvailability": {"mode": high_availability},
        "dataEncryption": {"type": "SystemManaged"},
        "network": {"publicNetworkAccess": "Disabled"},
    }
    identity: dict = {"type": "None"}

    if delegated_subnet_id is not None:
        properties["network"] = {
            "delegatedSubnetResourceId": delegated_subnet_id,
            "privateDnsZoneArmResourceId": private_dns_zone_id,
            "publicNetworkAccess": "Disabled",
        }
    if key_vault_key_uri is not None:
        properties["dataEncryption"] = {
            "type": "AzureKeyVault",
            "primaryKeyUri": key_vault_key_uri,
            "primaryUserAssignedIdentityId": user_assigned_identity_id,
        }
        identity = {
            "type": "UserAssigned",
            "userAssignedIdentities": {user_assigned_identity_id: {}},
        }

    return {
        "location": location,
        "sku": {"name": sku_name, "tier": "GeneralPurpose"},
        "identity": identity,
        "properties": properties,
    }
