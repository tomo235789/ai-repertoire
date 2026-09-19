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
    }
)


def _is_sensitive(key: str) -> bool:
    """区切り文字と大文字小文字を無視して、伏せるキーかを判定する"""
    return re.sub(r"[^a-z0-9]", "", key.lower()) in REDACTED_KEYS

_TIMESTAMP_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})$")


def _redact(key: str, value: Any) -> Any:
    """入れ子の dict と list も辿って、伏せるキーの値を置き換える"""
    if _is_sensitive(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {k: _redact(k, v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(key, v) for v in value]
    return value
_MAX_MESSAGE_CHARS = 100 * 1024
# LogEntry の上限は 256 KiB。メタデータのぶんを見込んで保守的に切る
MAX_ENTRY_BYTES = 200 * 1024

# Cloud Storage のバケット名。全体 222 文字、ドットで区切った各要素は 63 文字まで。
# goog 接頭辞、google の類似表記、IP アドレス形式は使えない
_BUCKET_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,61}[a-z0-9]$|^[a-z0-9]{3}$")
_IPV4_LIKE_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
# o と 0、l と 1 を入れ替えた表記も拒否される
_GOOGLE_LIKE_RE = re.compile(r"g[o0]{2}g[l1]e")


def _is_valid_bucket_name(name: str) -> bool:
    """Cloud Storage が受け付けるバケット名かを判定する"""
    if not 3 <= len(name) <= 222 or ".." in name:
        return False
    if name.startswith("goog") or _GOOGLE_LIKE_RE.search(name) or _IPV4_LIKE_RE.match(name):
        return False
    return all(_BUCKET_LABEL_RE.match(label) for label in name.split("."))

# Cloud Logging がシンクの転送先として受け付ける形式
_SINK_DESTINATION_RES = (
    re.compile(r"^bigquery\.googleapis\.com/projects/[^/]+/datasets/[A-Za-z0-9_]+$"),
    re.compile(
        r"^pubsub\.googleapis\.com/projects/[^/]+/topics/"
        r"(?!goog)[A-Za-z][A-Za-z0-9._~+%-]{2,254}$"
    ),
    re.compile(r"^logging\.googleapis\.com/projects/[^/]+$"),
    re.compile(r"^logging\.googleapis\.com/projects/[^/]+/locations/[^/]+/buckets/[^/]+$"),
)
SINK_DESTINATION_FORMS = (
    "storage.googleapis.com/<bucket>",
    "bigquery.googleapis.com/projects/<project>/datasets/<dataset>",
    "pubsub.googleapis.com/projects/<project>/topics/<topic>",
    "logging.googleapis.com/projects/<project>",
    "logging.googleapis.com/projects/<project>/locations/<location>/buckets/<bucket>",
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
            予約キーを fields に入れた、1 行が MAX_ENTRY_BYTES を超える場合
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
    line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    encoded = len(line.encode("utf-8"))
    if encoded > MAX_ENTRY_BYTES:
        raise ValueError(
            f"1 行が {MAX_ENTRY_BYTES} バイトを超える: {encoded} バイト。"
            "長い内容はストレージに置いて参照だけ載せる"
        )
    return line


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
    storage_prefix = "storage.googleapis.com/"
    if destination.startswith(storage_prefix):
        if not _is_valid_bucket_name(destination[len(storage_prefix) :]):
            raise ValueError(f"転送先のバケット名が不正: {destination!r}")
    elif not any(pattern.match(destination) for pattern in _SINK_DESTINATION_RES):
        raise ValueError(
            f"転送先は {SINK_DESTINATION_FORMS} のいずれかの形にする: {destination!r}"
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
