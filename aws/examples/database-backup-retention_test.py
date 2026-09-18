"""カード database-backup-retention の Contract を検証するテスト"""

from __future__ import annotations

import importlib
import json

import pytest

mod = importlib.import_module("database-backup-retention")
backup_settings = mod.backup_settings


def test_snapshot():
    """出力の全体像"""
    out = backup_settings(7, "17:00-17:30")
    assert out == {"BackupRetentionPeriod": 7, "CopyTagsToSnapshot": True, "PreferredBackupWindow": "17:00-17:30"}
    json.dumps(out)


def test_window_is_optional_and_copy_tags_defaults_true():
    """window 無しなら PreferredBackupWindow を出さない。copy_tags は既定 True"""
    assert backup_settings(14) == {"BackupRetentionPeriod": 14, "CopyTagsToSnapshot": True}
    assert backup_settings(14, copy_tags=False)["CopyTagsToSnapshot"] is False


def test_does_not_emit_identifier_or_apply_immediately():
    """DBInstanceIdentifier と ApplyImmediately は呼び出し側が決める（出力に含めない）"""
    out = backup_settings(7)
    assert "DBInstanceIdentifier" not in out
    assert "ApplyImmediately" not in out


def test_retention_boundaries():
    """1 と 35 は許可。36 と負数は ValueError"""
    assert backup_settings(1)["BackupRetentionPeriod"] == 1
    assert backup_settings(35)["BackupRetentionPeriod"] == 35
    for bad in (36, -1):
        with pytest.raises(ValueError):
            backup_settings(bad)
    with pytest.raises(TypeError):
        backup_settings(7.0)
    with pytest.raises(TypeError):
        backup_settings(True)


def test_zero_retention_is_rejected_with_explanation():
    """0 は自動バックアップの無効化なので ValueError。メッセージで別関数を案内する"""
    with pytest.raises(ValueError, match="無効化"):
        backup_settings(0)


def test_window_format_and_length():
    """hh24:mi-hh24:mi 以外、30 分未満は ValueError。日付をまたぐ枠は許可"""
    for bad in ("5:00-5:30", "17:00", "24:00-00:30", "17:00-17:29", "17:00-17:00", "17:00 - 17:30", "1700-1730"):
        with pytest.raises(ValueError):
            backup_settings(7, bad)
    assert backup_settings(7, "23:45-00:15")["PreferredBackupWindow"] == "23:45-00:15"
    assert backup_settings(7, "00:00-01:00")["PreferredBackupWindow"] == "00:00-01:00"
