"""カード storage-object-versioning: バケットの版管理と保持の設定を組み立てる純粋関数。

`google-cloud-storage` の `create_bucket` / `Bucket.patch` に渡すプロパティと、
旧版を整理するライフサイクル規則を返す。API は呼ばない。
"""

from __future__ import annotations


def versioning_config(
    *,
    keep_newer_versions: int = 3,
    delete_noncurrent_after_days: int = 30,
    soft_delete_retention_days: int = 7,
    retention_period_seconds: int | None = None,
) -> dict:
    """版管理と、旧版の整理と、誤削除からの復旧の設定を返す。

    Args:
        keep_newer_versions: 旧版を消すときに必ず残す新しい版の数。1 以上
        delete_noncurrent_after_days: 旧版を最新でなくなってからこの日数で削除
        soft_delete_retention_days: 論理削除の保持日数。7〜90
        retention_period_seconds: バケットの保持期間。None なら設定しない

    Returns:
        properties と lifecycle_rules を持つ dict

    Raises:
        ValueError: 残す版の数が 1 未満、旧版の削除日数が 1 未満、
            論理削除の保持日数が 7〜90 の外、保持期間が 1 秒未満の場合
    """
    if keep_newer_versions < 1:
        raise ValueError(f"残す版の数は 1 以上: {keep_newer_versions}")
    if delete_noncurrent_after_days < 1:
        raise ValueError(f"旧版の削除日数は 1 以上: {delete_noncurrent_after_days}")
    if not 7 <= soft_delete_retention_days <= 90:
        raise ValueError(f"論理削除の保持日数は 7〜90: {soft_delete_retention_days}")
    if retention_period_seconds is not None and retention_period_seconds < 1:
        raise ValueError(f"保持期間は 1 秒以上: {retention_period_seconds}")

    properties: dict = {
        "versioning": {"enabled": True},
        "softDeletePolicy": {"retentionDurationSeconds": str(soft_delete_retention_days * 86400)},
    }
    if retention_period_seconds is not None:
        properties["retentionPolicy"] = {"retentionPeriod": str(retention_period_seconds)}

    lifecycle = [
        {
            "action": {"type": "Delete"},
            "condition": {
                "daysSinceNoncurrentTime": delete_noncurrent_after_days,
                "numNewerVersions": keep_newer_versions,
            },
        }
    ]
    return {"properties": properties, "lifecycle_rules": lifecycle}
