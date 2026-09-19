"""カード observability-structured-logs: 構造化ログの集約設定を組み立てる純粋関数。

`azure-mgmt-monitor` の `diagnostic_settings.create_or_update` に渡す引数と、
アプリが出す 1 行分の JSON ログを作る関数を返す。API は呼ばず、時刻も自分で取らない。
"""

from __future__ import annotations

import json
import re
from typing import Any

_MAX_MESSAGE_CHARS = 32 * 1024
_SEVERITIES = ("Verbose", "Information", "Warning", "Error", "Critical")

# ログに出してはいけないキー（値ごと落とす）
# 区切り文字と大文字小文字を落としてから照合する
REDACTED_KEYS = frozenset(
    {
        "password",
        "passwd",
        "secret",
        "clientsecret",
        "token",
        "accesstoken",
        "refreshtoken",
        "authorization",
        "apikey",
        "xapikey",
        "accesskey",
        "privatekey",
        "connectionstring",
        "credential",
        "credentials",
        "sasurl",
    }
)


def _is_sensitive(key: str) -> bool:
    """区切り文字と大文字小文字を無視して、伏せるキーかを判定する"""
    return re.sub(r"[^a-z0-9]", "", key.lower()) in REDACTED_KEYS
# 関数が自分で埋めるキー。追加項目で上書きさせない
RESERVED_KEYS = frozenset({"timestamp", "severity", "message", "operationId"})

# /subscriptions/<id>/resourceGroups/<rg>/providers/<provider>/<type>/<name>
_WORKSPACE_ID_RE = re.compile(
    r"^/subscriptions/[^/\r\n]+/resourceGroups/[^/\r\n]+"
    r"/providers/Microsoft\.OperationalInsights/workspaces/[^/\r\n]+$"
)
ARM_RESOURCE_ID_RE = re.compile(
    r"^/subscriptions/[^/\r\n]+/resourceGroups/[^/\r\n]+/providers/[^/\r\n]+(/[^/\r\n]+/[^/\r\n]+)+$"
)


def _redact(key: str, value: Any) -> Any:
    """入れ子の dict と list も辿って、伏せるキーの値を置き換える"""
    if _is_sensitive(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {k: _redact(k, v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(key, v) for v in value]
    return value
_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")


def log_line(
    timestamp: str,
    severity: str,
    message: str,
    *,
    operation_id: str | None = None,
    fields: dict[str, Any] | None = None,
) -> str:
    """1 行の構造化ログを JSON 文字列で返す。

    Args:
        timestamp: ISO 8601 のタイムスタンプ。呼び出し側が渡す
        severity: _SEVERITIES のいずれか
        message: 本文
        operation_id: 分散トレースの相関 ID
        fields: 追加の項目。秘密らしいキーは値ごと伏せる

    Raises:
        ValueError: タイムスタンプの形式違い、未知の重大度、本文が空か長すぎる場合
    """
    if not _TIMESTAMP_RE.fullmatch(timestamp):
        raise ValueError(f"タイムスタンプは ISO 8601 で渡す: {timestamp!r}")
    if severity not in _SEVERITIES:
        raise ValueError(f"重大度は {_SEVERITIES} のいずれか: {severity!r}")
    if not message:
        raise ValueError("message は空にできない")
    if len(message) > _MAX_MESSAGE_CHARS:
        raise ValueError(f"message が長すぎる: {len(message)} 文字")

    extra = dict(fields or {})
    conflicting = sorted(set(extra) & RESERVED_KEYS)
    if conflicting:
        raise ValueError(f"予約キーは fields に入れられない: {conflicting}")

    record: dict[str, Any] = {
        "timestamp": timestamp,
        "severity": severity,
        "message": message,
    }
    if operation_id is not None:
        record["operationId"] = operation_id
    for key, value in sorted(extra.items()):
        record[key] = _redact(key, value)
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def diagnostic_setting(
    workspace_id: str,
    log_categories: tuple[str, ...] | list[str],
    *,
    metrics: bool = True,
) -> dict:
    """リソースのログをワークスペースへ送る診断設定を返す。

    Args:
        workspace_id: Log Analytics ワークスペースの ARM ID
        log_categories: 送るログカテゴリ。1 件以上
        metrics: メトリックも送るか

    Raises:
        ValueError: ワークスペース ID の形式違い、カテゴリが空の場合

    Note:
        保持期間は診断設定では決まらない。ワークスペースかテーブルの設定で決める。
    """
    if not _WORKSPACE_ID_RE.fullmatch(workspace_id):
        raise ValueError(
            "ワークスペースは Microsoft.OperationalInsights/workspaces の ARM ID: "
            f"{workspace_id!r}"
        )
    categories = tuple(log_categories)
    if not categories:
        raise ValueError("log_categories は 1 件以上必要")
    return {
        "workspaceId": workspace_id,
        # 専用テーブルに入れる。既定の AzureDiagnostics は列数の上限が厳しい
        "logAnalyticsDestinationType": "Dedicated",
        "logs": [
            {"category": category, "enabled": True} for category in sorted(set(categories))
        ],
        "metrics": [{"category": "AllMetrics", "enabled": True}] if metrics else [],
    }
