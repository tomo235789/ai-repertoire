"""カード storage-object-versioning: Blob のバージョン管理と復元の設定を組み立てる純粋関数。

`azure-mgmt-storage` の `blob_services.set_service_properties` に渡す
BlobServiceProperties を返す。API は呼ばない。
"""

from __future__ import annotations


def versioning_config(
    *,
    blob_retention_days: int = 30,
    container_retention_days: int = 30,
    point_in_time_restore_days: int | None = None,
) -> dict:
    """バージョン管理・論理削除・ポイントインタイム復元の設定を返す。

    Args:
        blob_retention_days: Blob の論理削除の保持日数。1〜365
        container_retention_days: コンテナの論理削除の保持日数。1〜365
        point_in_time_restore_days: 復元できる過去の日数。None なら復元を使わない

    Returns:
        BlobServiceProperties にそのまま渡せる dict

    Raises:
        ValueError: 保持日数が 1〜365 の外、復元日数が 0 以下、
            復元日数が Blob の保持日数以上の場合
    """
    for label, days in (
        ("blob_retention_days", blob_retention_days),
        ("container_retention_days", container_retention_days),
    ):
        if not 1 <= days <= 365:
            raise ValueError(f"{label} は 1〜365 日: {days}")

    properties: dict = {
        "isVersioningEnabled": True,
        "deleteRetentionPolicy": {
            "enabled": True,
            "days": blob_retention_days,
            # 論理削除された版も保持期間のあいだ残す
            "allowPermanentDelete": False,
        },
        "containerDeleteRetentionPolicy": {
            "enabled": True,
            "days": container_retention_days,
        },
        # 変更フィードはポイントインタイム復元の前提
        "changeFeed": {"enabled": True},
        "restorePolicy": {"enabled": False},
    }

    if point_in_time_restore_days is not None:
        if point_in_time_restore_days < 1:
            raise ValueError(
                f"point_in_time_restore_days は 1 日以上: {point_in_time_restore_days}"
            )
        if point_in_time_restore_days >= blob_retention_days:
            raise ValueError(
                "point_in_time_restore_days は blob_retention_days より小さくする: "
                f"{point_in_time_restore_days} >= {blob_retention_days}"
            )
        properties["restorePolicy"] = {
            "enabled": True,
            "days": point_in_time_restore_days,
        }

    return properties
