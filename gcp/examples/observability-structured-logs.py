"""カード observability-structured-logs: 構造化ログとログシンクを組み立てる純粋関数。

Cloud Logging が解釈する 1 行の JSON と、`sinks.create` に渡す LogSink を返す。
API は呼ばず、現在時刻も取らない。
"""

from __future__ import annotations

import json
import re
from typing import Any

# Cloud Logging が特別扱いするキー。アプリの項目と混ざらないよう予約する
RESERVED_KEYS = frozenset({"severity", "message", "time", "logging.googleapis.com/trace",
                           "logging.googleapis.com/spanId", "httpRequest"})
SEVERITIES = ("DEBUG", "INFO", "NOTICE", "WARNING", "ERROR", "CRITICAL", "ALERT", "EMERGENCY")

# ログに出してはいけないキー（値ごと落とす）
REDACTED_KEYS = frozenset({"password", "secret", "token", "authorization", "api_key", "apikey"})

_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")


def _redact(key: str, value: Any) -> Any:
    """入れ子の dict と list も辿って、伏せるキーの値を置き換える"""
    if key.lower() in REDACTED_KEYS:
        return "[REDACTED]"
    if isinstance(value, dict):
        return {k: _redact(k, v) for k, v in value.items()}
    if isinstance(value, list):
        return [_redact(key, v) for v in value]
    return value
_MAX_MESSAGE_CHARS = 100 * 1024

# Cloud Logging がシンクの転送先として受け付ける形式
SINK_DESTINATION_PREFIXES = (
    "storage.googleapis.com/",
    "bigquery.googleapis.com/",
    "pubsub.googleapis.com/",
    "logging.googleapis.com/",
)


def log_line(
    timestamp: str,
    severity: str,
    message: str,
    *,
    trace: str | None = None,
    fields: dict[str, Any] | None = None,
) -> str:
    """Cloud Logging が構造化ログとして読む 1 行の JSON を返す。

    Args:
        timestamp: ISO 8601 のタイムスタンプ。呼び出し側が渡す
        severity: SEVERITIES のいずれか
        message: 本文
        trace: `projects/<id>/traces/<trace-id>` 形式のトレース名
        fields: 追加の項目。予約キーとは重ねられず、秘密らしいキーは伏せる

    Raises:
        ValueError: タイムスタンプの形式違い、未知の重大度、本文が空か長すぎる、
            予約キーを fields に入れた場合
    """
    if not _TIMESTAMP_RE.match(timestamp):
        raise ValueError(f"タイムスタンプは ISO 8601 で渡す: {timestamp!r}")
    if severity not in SEVERITIES:
        raise ValueError(f"重大度は {SEVERITIES} のいずれか: {severity!r}")
    if not message:
        raise ValueError("message は空にできない")
    if len(message) > _MAX_MESSAGE_CHARS:
        raise ValueError(f"message が長すぎる: {len(message)} 文字")

    extra = dict(fields or {})
    conflicting = sorted(set(extra) & RESERVED_KEYS)
    if conflicting:
        raise ValueError(f"予約キーは fields に入れられない: {conflicting}")

    record: dict[str, Any] = {"time": timestamp, "severity": severity, "message": message}
    if trace is not None:
        record["logging.googleapis.com/trace"] = trace
    for key, value in sorted(extra.items()):
        record[key] = _redact(key, value)
    return json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def log_sink(
    name: str,
    destination: str,
    log_filter: str,
    *,
    exclusions: dict[str, str] | None = None,
    use_partitioned_tables: bool = True,
) -> dict:
    """ログを別の場所へ流すシンクの設定を返す。

    Args:
        name: シンク名
        destination: 転送先。`storage.googleapis.com/...` などの完全名
        log_filter: 流すログを絞る式
        exclusions: 除外名 -> 除外する式
        use_partitioned_tables: BigQuery 転送で日付分割テーブルを使うか

    Raises:
        ValueError: 名前が空、転送先の形式違い、フィルタが空の場合
    """
    if not name:
        raise ValueError("name は空にできない")
    if not any(destination.startswith(prefix) for prefix in SINK_DESTINATION_PREFIXES):
        raise ValueError(
            f"転送先は {SINK_DESTINATION_PREFIXES} のいずれかで始める: {destination!r}"
        )
    if not log_filter:
        raise ValueError("log_filter は空にできない。全ログを流すと費用が跳ねる")

    sink: dict = {
        "name": name,
        "destination": destination,
        "filter": log_filter,
        "exclusions": [
            {"name": exclusion_name, "filter": expression, "disabled": False}
            for exclusion_name, expression in sorted((exclusions or {}).items())
        ],
    }
    if destination.startswith("bigquery.googleapis.com/"):
        sink["bigquery_options"] = {"use_partitioned_tables": use_partitioned_tables}
    return sink
