"""カード secret-kms-key: 顧客管理の暗号鍵を組み立てる純粋関数。

Cloud KMS の `keyRings.create` / `cryptoKeys.create` に渡すリソースと、
鍵を使わせる IAM バインディングを返す。API は呼ばない。
"""

from __future__ import annotations

import re

_NAME_RE = re.compile(r"^[a-zA-Z0-9_-]{1,63}$")
_RFC3339_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")

# EXTERNAL は外部鍵マネージャの URI を別に登録する手順が要るのでここでは扱わない
PROTECTION_LEVELS = ("SOFTWARE", "HSM")
# 保存データの暗号化に使う用途
PURPOSE = "ENCRYPT_DECRYPT"
# 用途ごとに選べるアルゴリズム
ALGORITHMS = ("GOOGLE_SYMMETRIC_ENCRYPTION",)

ENCRYPTER_DECRYPTER_ROLE = "roles/cloudkms.cryptoKeyEncrypterDecrypter"
# 鍵の破棄を待つ日数の下限。短くすると誤破棄を取り消せない
MIN_DESTROY_SCHEDULED_DAYS = 7


def customer_managed_key(
    project_id: str,
    location: str,
    key_ring: str,
    key_name: str,
    *,
    next_rotation_time: str,
    protection_level: str = "HSM",
    rotation_period_days: int = 90,
    destroy_scheduled_days: int = 30,
    encrypter_members: tuple[str, ...] | list[str] = (),
) -> dict:
    """保存データの暗号化に使う鍵と、その置き場と権限の設定を返す。

    Args:
        project_id: プロジェクト ID
        location: キーリングのロケーション。データと同じ場所にする
        key_ring: キーリング名
        key_name: 鍵の名前
        next_rotation_time: 最初のローテーション時刻。RFC 3339 の UTC
        protection_level: PROTECTION_LEVELS のいずれか
        rotation_period_days: 自動ローテーションの間隔。1 日以上
        destroy_scheduled_days: 破棄要求から実際に消えるまでの日数。7 日以上
        encrypter_members: 鍵で暗号化・復号できるメンバー

    Returns:
        key_ring / crypto_key / iam_binding を持つ dict

    Raises:
        ValueError: 名前の形式違い、未知の保護レベル、ローテーション間隔が 1 日未満、
            破棄待ちが 7 日未満、メンバーの形式違い、
            次回ローテーション時刻が RFC 3339 でない場合
    """
    for label, value in (("key_ring", key_ring), ("key_name", key_name)):
        if not _NAME_RE.match(value):
            raise ValueError(f"{label} の形式が不正: {value!r}")
    if not _RFC3339_RE.match(next_rotation_time):
        raise ValueError(
            f"次回ローテーション時刻は RFC 3339 の UTC で渡す: {next_rotation_time!r}"
        )
    if protection_level not in PROTECTION_LEVELS:
        raise ValueError(f"保護レベルは {PROTECTION_LEVELS} のいずれか: {protection_level!r}")
    if rotation_period_days < 1:
        raise ValueError(f"ローテーション間隔は 1 日以上: {rotation_period_days}")
    if destroy_scheduled_days < MIN_DESTROY_SCHEDULED_DAYS:
        raise ValueError(
            f"破棄待ちは {MIN_DESTROY_SCHEDULED_DAYS} 日以上: {destroy_scheduled_days}"
        )
    members = sorted(set(encrypter_members))
    for member in members:
        if ":" not in member:
            raise ValueError(f"メンバーは <種別>:<識別子> の形で指定する: {member!r}")

    key_ring_name = f"projects/{project_id}/locations/{location}/keyRings/{key_ring}"
    crypto_key_name = f"{key_ring_name}/cryptoKeys/{key_name}"

    return {
        "key_ring": {"parent": f"projects/{project_id}/locations/{location}", "key_ring_id": key_ring},
        "crypto_key": {
            "parent": key_ring_name,
            "crypto_key_id": key_name,
            "crypto_key": {
                "purpose": PURPOSE,
                "rotation_period": f"{rotation_period_days * 86400}s",
                # rotation_period だけでは自動ローテーションが始まらない
                "next_rotation_time": next_rotation_time,
                "destroy_scheduled_duration": f"{destroy_scheduled_days * 86400}s",
                "version_template": {
                    "protection_level": protection_level,
                    "algorithm": ALGORITHMS[0],
                },
            },
        },
        "iam_binding": {
            "resource": crypto_key_name,
            "role": ENCRYPTER_DECRYPTER_ROLE,
            "members": members,
        },
    }
