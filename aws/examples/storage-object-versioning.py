"""カード storage-object-versioning: S3 バケットのバージョニング設定を組み立てる純粋関数。

put_bucket_versioning の VersioningConfiguration を返す。API は呼ばない。
"""

from __future__ import annotations


def versioning_config(enabled: bool = True, mfa_delete: bool = False) -> dict[str, str]:
    """VersioningConfiguration を返す。

    enabled    : True なら "Enabled"、False なら "Suspended"（一度有効にしたバケットは "Disabled" に戻せない）
    mfa_delete : True なら MFADelete を "Enabled" にする。呼び出し側は put_bucket_versioning に
                 MFA="<serial> <code>" を付け、ルート資格情報で呼ぶ必要がある
    """
    config = {"Status": "Enabled" if enabled else "Suspended"}
    if mfa_delete:
        config["MFADelete"] = "Enabled"
    return config
