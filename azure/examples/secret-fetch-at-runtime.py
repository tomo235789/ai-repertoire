"""カード secret-fetch-at-runtime: 秘密を実行時に Key Vault から取る設定を組み立てる純粋関数。

アプリ設定に入れる Key Vault 参照の文字列と、必要なロール割り当てを返す。
秘密の値そのものは扱わず、API も呼ばない。
"""

from __future__ import annotations

import re
import uuid

_VAULT_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9-]{1,22}[a-zA-Z0-9]$")
_SECRET_RE = re.compile(r"^[a-zA-Z0-9-]{1,127}$")
_UUID_RE = re.compile(r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")

# Key Vault Secrets User（読み取りだけ。値の書き換えはできない）
SECRETS_USER_ROLE_ID = "4633458b-17de-408a-b874-0445c86b69e6"
_ASSIGNMENT_NAMESPACE = uuid.UUID("6ba7b814-9dad-11d1-80b4-00c04fd430c8")


def key_vault_reference(vault_name: str, secret_name: str, version: str | None = None) -> str:
    """アプリ設定に書く Key Vault 参照の文字列を返す。

    Args:
        vault_name: コンテナー（Key Vault）名
        secret_name: シークレット名
        version: バージョン。省略すると最新を追従する

    Raises:
        ValueError: 名前の形式違い、バージョンが 32 桁の 16 進でない場合
    """
    if not _VAULT_RE.fullmatch(vault_name):
        raise ValueError(f"Key Vault 名の形式が不正: {vault_name!r}")
    if not _SECRET_RE.fullmatch(secret_name):
        raise ValueError(f"シークレット名の形式が不正: {secret_name!r}")
    uri = f"https://{vault_name}.vault.azure.net/secrets/{secret_name}"
    if version is not None:
        if not re.fullmatch(r"[0-9a-f]{32}", version):
            raise ValueError(f"バージョンは 32 桁の 16 進: {version!r}")
        uri = f"{uri}/{version}"
    return f"@Microsoft.KeyVault(SecretUri={uri})"


def runtime_secret_config(
    vault_name: str,
    secrets: dict[str, str],
    principal_id: str,
    *,
    subscription_id: str,
    resource_group: str,
    pin_versions: dict[str, str] | None = None,
) -> dict:
    """アプリ設定と、読み取りに必要なロール割り当てを返す。

    Args:
        vault_name: Key Vault 名
        secrets: 環境変数名 -> シークレット名
        principal_id: 読み取るワークロードのマネージド ID のオブジェクト ID
        subscription_id: サブスクリプション ID
        resource_group: Key Vault があるリソースグループ
        pin_versions: 環境変数名 -> 固定するバージョン

    Returns:
        app_settings と role_assignment を持つ dict

    Raises:
        ValueError: secrets が空、principal_id が GUID でない、
            pin_versions に secrets に無いキーがある場合
    """
    if not secrets:
        raise ValueError("secrets は 1 件以上必要")
    if not _UUID_RE.fullmatch(principal_id):
        raise ValueError(f"principal_id は GUID を指定する: {principal_id!r}")
    pin_versions = dict(pin_versions or {})
    unknown = set(pin_versions) - set(secrets)
    if unknown:
        raise ValueError(f"secrets に無い環境変数のバージョンは固定できない: {sorted(unknown)}")

    app_settings = [
        {
            "name": env_name,
            "value": key_vault_reference(vault_name, secret_name, pin_versions.get(env_name)),
        }
        for env_name, secret_name in sorted(secrets.items())
    ]

    scope = (
        f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}"
        f"/providers/Microsoft.KeyVault/vaults/{vault_name}"
    )
    return {
        "app_settings": app_settings,
        "role_assignment": {
            "scope": scope,
            "role_assignment_name": str(
                uuid.uuid5(_ASSIGNMENT_NAMESPACE, f"{scope}|{principal_id}|secrets-user")
            ),
            "parameters": {
                "properties": {
                    "roleDefinitionId": (
                        f"/subscriptions/{subscription_id}"
                        f"/providers/Microsoft.Authorization/roleDefinitions/"
                        f"{SECRETS_USER_ROLE_ID}"
                    ),
                    "principalId": principal_id,
                    "principalType": "ServicePrincipal",
                }
            },
        },
    }
