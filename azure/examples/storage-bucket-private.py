"""カード storage-bucket-private: 非公開のオブジェクトストレージ構成を組み立てる純粋関数。

`azure-mgmt-storage` の `storage_accounts.begin_create` / `blob_containers.create` と、
`azure-mgmt-authorization` の `role_assignments.create` に渡す引数を返す。API は呼ばない。
"""

from __future__ import annotations

import re
import uuid

_ACCOUNT_RE = re.compile(r"^[a-z0-9]{3,24}$")
_CONTAINER_RE = re.compile(r"^[a-z0-9]([a-z0-9-]{1,61}[a-z0-9])$")

# Storage Blob Data Reader（テナントに依らず固定の組み込みロール GUID）
BLOB_DATA_READER_ROLE_ID = "2a2b9908-6ea1-4ae2-8e65-a410df84e7d1"
PRINCIPAL_TYPES = ("User", "Group", "ServicePrincipal")
_ASSIGNMENT_NAMESPACE = uuid.UUID("6ba7b812-9dad-11d1-80b4-00c04fd430c8")


def _split_key_uri(key_uri: str) -> tuple[str, str, str]:
    """鍵の URI を (金庫の URI, 鍵名, 版) に分ける。版を省いた URI なら版は空文字。

    Raises:
        ValueError: `https://<vault>/keys/<name>[/<version>]` の形でない場合
    """
    match = re.match(r"^(https://[^/]+)/keys/([^/]+)(?:/([^/]+))?/?$", key_uri)
    if match is None:
        raise ValueError(
            f"鍵の URI は https://<vault>/keys/<name>[/<version>] の形で渡す: {key_uri!r}"
        )
    vault_uri, key_name, key_version = match.groups()
    return vault_uri, key_name, key_version or ""


def private_container_config(
    account_name: str,
    container_name: str,
    location: str,
    *,
    subscription_id: str,
    resource_group: str,
    key_vault_key_uri: str | None = None,
    reader_principal_ids: tuple[str, ...] | list[str] = (),
    reader_principal_type: str = "ServicePrincipal",
    tags: dict[str, str] | None = None,
    allowed_ip_rules: tuple[str, ...] | list[str] = (),
) -> dict:
    """公開アクセスを完全に塞いだストレージアカウントとコンテナの構成を返す。

    Args:
        account_name: ストレージアカウント名。小文字英数字 3〜24 文字で Azure 全体で一意
        container_name: コンテナ名。小文字英数字とハイフンで 3〜63 文字
        location: リージョン名
        subscription_id: サブスクリプション ID
        resource_group: リソースグループ名
        key_vault_key_uri: 顧客管理鍵の URI。省略すると Microsoft 管理鍵
        reader_principal_ids: 読み取りを許すプリンシパルのオブジェクト ID
        reader_principal_type: プリンシパルの種別。User / Group / ServicePrincipal
        tags: アカウントに付けるタグ
        allowed_ip_rules: 例外的に許可する送信元 IP。空なら全拒否

    Returns:
        account / container / role_assignments を持つ dict

    Raises:
        ValueError: 名前の形式違い、`allUsers` のような匿名プリンシパルの指定
    """
    if not _ACCOUNT_RE.match(account_name):
        raise ValueError(f"ストレージアカウント名は小文字英数字 3〜24 文字: {account_name!r}")
    if not _CONTAINER_RE.match(container_name) or not 3 <= len(container_name) <= 63:
        raise ValueError(f"コンテナ名の形式が不正: {container_name!r}")
    if reader_principal_type not in PRINCIPAL_TYPES:
        raise ValueError(f"プリンシパル種別は {PRINCIPAL_TYPES} のいずれか: {reader_principal_type!r}")
    for pid in reader_principal_ids:
        if pid in {"allUsers", "allAuthenticatedUsers", ""}:
            raise ValueError(f"匿名・全員のプリンシパルには読み取りを与えない: {pid!r}")

    account: dict = {
        "location": location,
        "sku": {"name": "Standard_GRS"},
        "kind": "StorageV2",
        "properties": {
            # 公開アクセスの三重の封じ込め
            "allowBlobPublicAccess": False,
            "publicNetworkAccess": "Disabled" if not allowed_ip_rules else "Enabled",
            "networkAcls": {
                "defaultAction": "Deny",
                "bypass": "AzureServices",
                "ipRules": [{"value": ip, "action": "Allow"} for ip in allowed_ip_rules],
                "virtualNetworkRules": [],
            },
            # 共有キーを無効にして Entra ID の認証だけを通す
            "allowSharedKeyAccess": False,
            "minimumTlsVersion": "TLS1_2",
            "supportsHttpsTrafficOnly": True,
            "encryption": {
                "services": {
                    "blob": {"enabled": True, "keyType": "Account"},
                    "file": {"enabled": True, "keyType": "Account"},
                },
                "requireInfrastructureEncryption": True,
                "keySource": "Microsoft.Storage",
            },
        },
    }
    if tags:
        account["tags"] = dict(sorted(tags.items()))
    if key_vault_key_uri is not None:
        vault_uri, key_vault_name, key_version = _split_key_uri(key_vault_key_uri)
        account["identity"] = {"type": "SystemAssigned"}
        encryption = account["properties"]["encryption"]
        encryption["keySource"] = "Microsoft.Keyvault"
        # Azure Storage は鍵の URI をまとめて受け取らない。金庫の URI と鍵名を分けて渡す
        encryption["keyvaultproperties"] = {
            "keyvaulturi": vault_uri,
            "keyname": key_vault_name,
            "keyversion": key_version,
        }

    container = {
        "resource_group_name": resource_group,
        "account_name": account_name,
        "container_name": container_name,
        "blob_container": {"properties": {"publicAccess": "None", "metadata": {}}},
    }

    scope = (
        f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        f"/providers/Microsoft.Storage/storageAccounts/{account_name}"
        f"/blobServices/default/containers/{container_name}"
    )
    role_assignments = [
        {
            "scope": scope,
            "role_assignment_name": str(
                uuid.uuid5(_ASSIGNMENT_NAMESPACE, f"{scope}|{pid}|reader")
            ),
            "parameters": {
                "properties": {
                    "roleDefinitionId": (
                        f"/subscriptions/{subscription_id}"
                        f"/providers/Microsoft.Authorization/roleDefinitions/"
                        f"{BLOB_DATA_READER_ROLE_ID}"
                    ),
                    "principalId": pid,
                    "principalType": reader_principal_type,
                }
            },
        }
        for pid in reader_principal_ids
    ]

    return {"account": account, "container": container, "role_assignments": role_assignments}
