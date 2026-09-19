"""カード database-backup-retention: バックアップと保持期間の設定を組み立てる純粋関数。

`azure-mgmt-rdbms` の PostgreSQL フレキシブルサーバーに渡す backup プロパティを返す。
API は呼ばない。

長期保持（週次・月次・年次）はサーバーのプロパティではなく Azure Backup の
バックアップポリシーで設定するため、この関数では扱わない。
"""

from __future__ import annotations

# 自動バックアップの保持日数の範囲
MIN_RETENTION_DAYS = 7
MAX_RETENTION_DAYS = 35


def backup_retention_config(
    *,
    retention_days: int = 35,
    geo_redundant: bool = True,
) -> dict:
    """自動バックアップの設定を、作成用と更新用に分けて返す。

    Args:
        retention_days: 自動バックアップの保持日数。7〜35
        geo_redundant: ペアリージョンへバックアップを複製するか。作成時にしか決められない

    Returns:
        backup_on_create（作成時の body）と backup_on_update（更新時の body）を持つ dict

    Raises:
        ValueError: 保持日数が 7〜35 の外の場合
    """
    if not MIN_RETENTION_DAYS <= retention_days <= MAX_RETENTION_DAYS:
        raise ValueError(
            f"保持日数は {MIN_RETENTION_DAYS}〜{MAX_RETENTION_DAYS} 日: {retention_days}"
        )

    return {
        # サーバー作成時の body。地理冗長は作成時にしか決められない
        "backup_on_create": {
            "backupRetentionDays": retention_days,
            "geoRedundantBackup": "Enabled" if geo_redundant else "Disabled",
        },
        # 既存サーバーの更新用。作成時にしか決められないキーを含めない
        "backup_on_update": {"backupRetentionDays": retention_days},
    }
