"""カード storage-bucket-lifecycle: 保持期間で S3 オブジェクトを移行・削除するライフサイクル設定を組み立てる純粋関数。

put_bucket_lifecycle_configuration の LifecycleConfiguration を返す。API は呼ばない。
"""

from __future__ import annotations

from typing import Any

# 移行先に指定できるストレージクラス
STORAGE_CLASSES = frozenset(
    {"STANDARD_IA", "ONEZONE_IA", "INTELLIGENT_TIERING", "GLACIER_IR", "GLACIER", "DEEP_ARCHIVE"}
)
# S3 Standard から最低 30 日置かないと移行できないクラス
_MIN_30_DAYS_CLASSES = frozenset({"STANDARD_IA", "ONEZONE_IA"})


def _positive_int_or_none(value: int | None, label: str) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise ValueError(f"{label} must be a positive integer, got {value!r}")


def lifecycle_rules(
    transition_days: int | None,
    expiration_days: int | None,
    noncurrent_days: int | None,
    abort_multipart_days: int | None,
    prefix: str = "",
    storage_class: str = "STANDARD_IA",
) -> dict[str, Any]:
    """1 つのルールからなる LifecycleConfiguration を返す。

    transition_days      : 作成から何日で storage_class へ移行するか（None なら移行しない）
    expiration_days      : 作成から何日で現行バージョンを削除するか（None なら削除しない）
    noncurrent_days      : 非現行バージョンを何日後に削除するか（None なら削除しない）
    abort_multipart_days : 未完了のマルチパートアップロードを何日後に破棄するか（None なら破棄しない）
    prefix               : 対象キーの接頭辞。"" は全オブジェクト
    """
    for value, label in (
        (transition_days, "transition_days"),
        (expiration_days, "expiration_days"),
        (noncurrent_days, "noncurrent_days"),
        (abort_multipart_days, "abort_multipart_days"),
    ):
        _positive_int_or_none(value, label)
    if all(v is None for v in (transition_days, expiration_days, noncurrent_days, abort_multipart_days)):
        raise ValueError("at least one of transition/expiration/noncurrent/abort days is required")
    if storage_class not in STORAGE_CLASSES:
        raise ValueError(f"unsupported storage class: {storage_class!r}")
    if transition_days is not None and expiration_days is not None and transition_days >= expiration_days:
        raise ValueError(
            f"transition_days ({transition_days}) must be less than expiration_days ({expiration_days})"
        )
    if transition_days is not None and storage_class in _MIN_30_DAYS_CLASSES and transition_days < 30:
        raise ValueError(f"transition to {storage_class} requires at least 30 days, got {transition_days}")

    rule: dict[str, Any] = {
        "ID": f"lifecycle-{prefix}" if prefix else "lifecycle",
        "Filter": {"Prefix": prefix},
        "Status": "Enabled",
    }
    if transition_days is not None:
        rule["Transitions"] = [{"Days": transition_days, "StorageClass": storage_class}]
    if expiration_days is not None:
        rule["Expiration"] = {"Days": expiration_days}
    if noncurrent_days is not None:
        rule["NoncurrentVersionExpiration"] = {"NoncurrentDays": noncurrent_days}
    if abort_multipart_days is not None:
        rule["AbortIncompleteMultipartUpload"] = {"DaysAfterInitiation": abort_multipart_days}
    return {"Rules": [rule]}
