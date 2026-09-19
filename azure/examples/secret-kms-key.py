"""カード secret-kms-key: 顧客管理の暗号鍵とコンテナーの設定を組み立てる純粋関数。

`azure-mgmt-keyvault` の `vaults.begin_create_or_update` と `keys.create_if_not_exist`
に渡す引数を返す。鍵そのものは作らず、API も呼ばない。
"""

from __future__ import annotations

import re

_VAULT_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9-]{1,22}[a-zA-Z0-9]$")
_KEY_RE = re.compile(r"^[a-zA-Z0-9-]{1,127}$")

# 暗号化・復号に使う鍵に許す操作（署名や鍵のエクスポートは含めない）
WRAP_KEY_OPS = ("wrapKey", "unwrapKey", "encrypt", "decrypt")
_ALLOWED_KEY_TYPES = {"RSA": (3072, 4096), "RSA-HSM": (3072, 4096)}
# Key Vault が受け付けるローテーションポリシーの下限
MIN_ROTATION_DAYS = 7
# 期限 30 日前に通知するので、有効期間はそれより長くする
NOTIFY_BEFORE_EXPIRY_DAYS = 30
MIN_EXPIRY_DAYS = NOTIFY_BEFORE_EXPIRY_DAYS + 1
# ローテーションから期限切れまでに要る最短の間隔
MIN_ROTATION_TO_EXPIRY_GAP = 7


def customer_managed_key(
    vault_name: str,
    key_name: str,
    location: str,
    *,
    tenant_id: str,
    key_type: str = "RSA-HSM",
    key_size: int = 3072,
    rotation_period_days: int = 365,
    expiry_days: int = 730,
    purge_protection: bool = True,
    soft_delete_retention_days: int = 90,
) -> dict:
    """保存データの暗号化に使う鍵と、その置き場の設定を返す。

    Args:
        vault_name: Key Vault 名
        key_name: 鍵の名前
        location: リージョン
        tenant_id: テナント ID
        key_type: "RSA" か "RSA-HSM"
        key_size: 3072 か 4096
        rotation_period_days: 自動ローテーションの間隔
        expiry_days: 鍵の有効期間。31 日以上かつローテーション間隔より 7 日以上長くする
        purge_protection: 消去保護。True にすると論理削除後の完全削除を禁じる
        soft_delete_retention_days: 論理削除の保持日数。7〜90

    Returns:
        vault と key と rotation_policy を持つ dict

    Raises:
        ValueError: 名前の形式違い、鍵の種類やサイズが許可外、保持日数が範囲外、
            有効期間がローテーション間隔以下、消去保護を無効にしようとした場合
    """
    if not _VAULT_RE.fullmatch(vault_name):
        raise ValueError(f"Key Vault 名の形式が不正: {vault_name!r}")
    if not _KEY_RE.fullmatch(key_name):
        raise ValueError(f"鍵の名前の形式が不正: {key_name!r}")
    if key_type not in _ALLOWED_KEY_TYPES:
        raise ValueError(f"鍵の種類は RSA か RSA-HSM: {key_type!r}")
    if key_size not in _ALLOWED_KEY_TYPES[key_type]:
        raise ValueError(f"鍵長が許可外: {key_size}")
    if not 7 <= soft_delete_retention_days <= 90:
        raise ValueError(f"論理削除の保持日数は 7〜90: {soft_delete_retention_days}")
    if rotation_period_days < MIN_ROTATION_DAYS:
        raise ValueError(
            f"ローテーション間隔は {MIN_ROTATION_DAYS} 日以上: {rotation_period_days}"
        )
    if expiry_days < MIN_EXPIRY_DAYS:
        raise ValueError(f"有効期間は {MIN_EXPIRY_DAYS} 日以上: {expiry_days}")
    if expiry_days < rotation_period_days + MIN_ROTATION_TO_EXPIRY_GAP:
        raise ValueError(
            f"有効期間はローテーション間隔より {MIN_ROTATION_TO_EXPIRY_GAP} 日以上長くする: "
            f"{expiry_days} < {rotation_period_days} + {MIN_ROTATION_TO_EXPIRY_GAP}"
        )
    if not purge_protection:
        raise ValueError(
            "消去保護を切ると、暗号化したデータを復号できなくする操作が取り消せなくなる"
        )

    vault = {
        "location": location,
        "properties": {
            "tenantId": tenant_id,
            "sku": {"family": "A", "name": "premium" if key_type.endswith("HSM") else "standard"},
            # アクセスポリシーではなく RBAC で権限を管理する
            "enableRbacAuthorization": True,
            "enableSoftDelete": True,
            "softDeleteRetentionInDays": soft_delete_retention_days,
            "enablePurgeProtection": True,
            "publicNetworkAccess": "Disabled",
            "networkAcls": {"defaultAction": "Deny", "bypass": "AzureServices"},
        },
    }

    key = {
        "properties": {
            "kty": key_type,
            "keySize": key_size,
            "keyOps": list(WRAP_KEY_OPS),
            "attributes": {"enabled": True, "exportable": False},
        }
    }

    rotation_policy = {
        "lifetimeActions": [
            {
                # 期限からの逆算ではなく作成からの経過で回す。
                # そうしないと最初の版がローテーションされない
                "trigger": {"timeAfterCreate": f"P{rotation_period_days}D"},
                "action": {"type": "Rotate"},
            },
            {
                "trigger": {"timeBeforeExpiry": f"P{NOTIFY_BEFORE_EXPIRY_DAYS}D"},
                "action": {"type": "Notify"},
            },
        ],
        "attributes": {"expiryTime": f"P{expiry_days}D"},
    }

    return {"vault": vault, "key": key, "rotation_policy": rotation_policy}
