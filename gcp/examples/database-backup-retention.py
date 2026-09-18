"""カード database-backup-retention: バックアップと保持期間の設定を組み立てる純粋関数。

Cloud SQL の `settings.backupConfiguration` に渡す dict を返す。API は呼ばない。
"""

from __future__ import annotations

import re

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")

# 自動バックアップの保持数
MIN_BACKUP_COUNT = 7
MAX_BACKUP_COUNT = 365
# ポイントインタイム復旧のログ保持日数
# Enterprise エディションの上限。Enterprise Plus なら 35 日まで伸ばせる
MAX_TRANSACTION_LOG_DAYS = 7


def backup_retention_config(
    *,
    start_time: str = "18:00",
    retained_backups: int = 30,
    point_in_time_recovery: bool = True,
    transaction_log_retention_days: int = 7,
    location: str | None = None,
) -> dict:
    """自動バックアップとポイントインタイム復旧の設定を返す。

    Args:
        start_time: バックアップ開始時刻。UTC の "HH:MM"
        retained_backups: 残す自動バックアップの数。7〜365
        point_in_time_recovery: ポイントインタイム復旧を有効にするか
        transaction_log_retention_days: トランザクションログの保持日数。1〜7
            （Enterprise エディションの上限。Enterprise Plus なら 35 日まで伸ばせる）
        location: バックアップの保存先。None ならインスタンスと同じ多リージョン

    Returns:
        backupConfiguration にそのまま渡せる dict

    Raises:
        ValueError: 時刻の形式違い、保持数が 7〜365 の外、
            ログ保持日数が 1〜7 の外、
            ポイントインタイム復旧を切ってログ保持だけ指定した場合
    """
    if not _TIME_RE.match(start_time):
        raise ValueError(f"開始時刻は UTC の HH:MM で指定する: {start_time!r}")
    if not MIN_BACKUP_COUNT <= retained_backups <= MAX_BACKUP_COUNT:
        raise ValueError(
            f"保持数は {MIN_BACKUP_COUNT}〜{MAX_BACKUP_COUNT}: {retained_backups}"
        )
    if not 1 <= transaction_log_retention_days <= MAX_TRANSACTION_LOG_DAYS:
        raise ValueError(
            f"ログ保持日数は 1〜{MAX_TRANSACTION_LOG_DAYS}: {transaction_log_retention_days}"
        )
    if not point_in_time_recovery and transaction_log_retention_days != 7:
        raise ValueError(
            "ポイントインタイム復旧を切るならログ保持日数は指定しない"
        )

    config: dict = {
        "enabled": True,
        "startTime": start_time,
        "pointInTimeRecoveryEnabled": point_in_time_recovery,
        "backupRetentionSettings": {
            "retentionUnit": "COUNT",
            "retainedBackups": retained_backups,
        },
    }
    if point_in_time_recovery:
        config["transactionLogRetentionDays"] = transaction_log_retention_days
    if location is not None:
        config["location"] = location
    return config
