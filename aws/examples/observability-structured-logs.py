"""カード observability-structured-logs: JSON 構造化ログのロググループと、エラー行を数えるメトリクスフィルター

logs.create_log_group / put_retention_policy / put_metric_filter の kwargs を返す（CloudWatch Logs の kwargs は lowerCamelCase）。
"""

from __future__ import annotations

import re
from typing import Any, Mapping

_LOG_GROUP_NAME_RE = re.compile(r"^[A-Za-z0-9_./#-]{1,512}$")
_KMS_KEY_ARN_RE = re.compile(r"^arn:aws(?:-[a-z]+)?:kms:[a-z0-9-]+:\d{12}:key/[0-9a-f-]{36}$")
_METRIC_NAME_RE = re.compile(r"^[A-Za-z0-9_.:/#-]{1,255}$")

# put_retention_policy の retentionInDays が受け付ける値
RETENTION_CHOICES = (
    1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1096, 1827, 2192, 2557, 2922, 3288, 3653,
)
DEFAULT_ERROR_PATTERN = '{ $.level = "error" }'


def log_group_with_error_metric(
    name: str,
    retention_days: int,
    kms_key_id: str | None = None,
    error_pattern: str = DEFAULT_ERROR_PATTERN,
    metric_namespace: str = "Application",
    *,
    metric_name: str = "ErrorCount",
    tags: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    """ロググループ作成・保持期間・エラーメトリクスフィルターの kwargs を返す。

    :param name: ロググループ名（`/app/api` のような階層名）
    :param retention_days: 保持日数。RETENTION_CHOICES のいずれか
    :param kms_key_id: 暗号化に使う CMK の **鍵 ARN**（CloudWatch Logs はエイリアスや鍵 ID を受け付けない）。None なら AWS 管理の暗号化
    :param error_pattern: エラー行を検出するフィルターパターン。既定は JSON の level=error
    :param metric_namespace: メトリクスの名前空間（AWS/ で始まる名前は不可）
    :param metric_name: メトリクス名
    """
    if not _LOG_GROUP_NAME_RE.match(name):
        raise ValueError(f"ロググループ名が不正: {name!r}（英数字と _ - / . # で 512 文字以内）")
    if isinstance(retention_days, bool) or retention_days not in RETENTION_CHOICES:
        raise ValueError(f"retention_days は {RETENTION_CHOICES} のいずれか（実際: {retention_days!r}）")
    if kms_key_id is not None and not _KMS_KEY_ARN_RE.match(kms_key_id):
        raise ValueError(f"kms_key_id は鍵 ARN（arn:aws:kms:...:key/...）で渡す: {kms_key_id!r}")
    if not error_pattern.strip():
        raise ValueError("error_pattern が空。空パターンは全行に一致してしまう")
    if not metric_namespace or metric_namespace.startswith("AWS/"):
        raise ValueError(f"metric_namespace は空でなく AWS/ で始まらない名前: {metric_namespace!r}")
    if not _METRIC_NAME_RE.match(metric_name):
        raise ValueError(f"metric_name が不正: {metric_name!r}")

    create_log_group: dict[str, Any] = {"logGroupName": name, "logGroupClass": "STANDARD"}
    if kms_key_id:
        create_log_group["kmsKeyId"] = kms_key_id
    if tags:
        create_log_group["tags"] = dict(sorted(tags.items()))

    return {
        "create_log_group": create_log_group,
        "put_retention_policy": {"logGroupName": name, "retentionInDays": retention_days},
        "put_metric_filter": {
            "logGroupName": name,
            "filterName": f"{metric_name}Filter",
            "filterPattern": error_pattern,
            "metricTransformations": [
                {
                    "metricName": metric_name,
                    "metricNamespace": metric_namespace,
                    "metricValue": "1",
                    "defaultValue": 0.0,
                    "unit": "Count",
                }
            ],
        },
    }
