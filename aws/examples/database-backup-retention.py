"""カード database-backup-retention: 自動バックアップの保持期間とバックアップウィンドウ

rds.modify_db_instance に DBInstanceIdentifier と合わせて展開する kwargs を返す（create_db_instance にも同じキーで渡せる）。
保持期間 0（自動バックアップの無効化）はこの関数では作れない。
"""

from __future__ import annotations

import re
from typing import Any

MIN_RETENTION_DAYS = 1
MAX_RETENTION_DAYS = 35
MIN_WINDOW_MINUTES = 30

_WINDOW_RE = re.compile(r"^(?P<sh>[01]\d|2[0-3]):(?P<sm>[0-5]\d)-(?P<eh>[01]\d|2[0-3]):(?P<em>[0-5]\d)$")


def _window_minutes(window: str) -> int:
    """`hh24:mi-hh24:mi`（UTC）の長さを分で返す。日付をまたぐ指定も許す。形式違いは ValueError"""
    m = _WINDOW_RE.match(window)
    if not m:
        raise ValueError(f"backup_window は UTC の hh24:mi-hh24:mi 形式: {window!r}")
    start = int(m["sh"]) * 60 + int(m["sm"])
    end = int(m["eh"]) * 60 + int(m["em"])
    return (end - start) % (24 * 60)


def backup_settings(
    retention_days: int,
    backup_window: str | None = None,
    copy_tags: bool = True,
) -> dict[str, Any]:
    """バックアップ関連の kwargs を返す。

    :param retention_days: 自動バックアップの保持日数（1〜35）。0 は受け付けない
    :param backup_window: UTC の `hh24:mi-hh24:mi`。30 分以上。None なら AWS がリージョンごとの既定枠から選ぶ
    :param copy_tags: インスタンスのタグをスナップショットにも付ける
    """
    if isinstance(retention_days, bool) or not isinstance(retention_days, int):
        raise TypeError("retention_days は int")
    if retention_days == 0:
        raise ValueError(
            "retention_days=0 は自動バックアップの無効化を意味する。誤設定を防ぐため、この関数では作れない。"
            "無効化が本当に必要なら、明示的な別関数として書く"
        )
    if not MIN_RETENTION_DAYS <= retention_days <= MAX_RETENTION_DAYS:
        raise ValueError(f"retention_days は {MIN_RETENTION_DAYS}〜{MAX_RETENTION_DAYS}（実際: {retention_days}）")

    kwargs: dict[str, Any] = {"BackupRetentionPeriod": retention_days, "CopyTagsToSnapshot": bool(copy_tags)}
    if backup_window is not None:
        minutes = _window_minutes(backup_window)
        if minutes < MIN_WINDOW_MINUTES:
            raise ValueError(f"backup_window は {MIN_WINDOW_MINUTES} 分以上（実際: {minutes} 分）")
        kwargs["PreferredBackupWindow"] = backup_window
    return kwargs
