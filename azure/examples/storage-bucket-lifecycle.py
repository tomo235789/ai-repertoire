"""カード storage-bucket-lifecycle: Blob の保持期間ルールを組み立てる純粋関数。

`azure-mgmt-storage` の `management_policies.create_or_update` に渡す
ManagementPolicy の properties を返す。API は呼ばない。
"""

from __future__ import annotations


def lifecycle_policy(
    rule_name: str,
    *,
    prefix_match: tuple[str, ...] | list[str] = (),
    days_to_cool: int | None = 30,
    days_to_archive: int | None = 90,
    days_to_delete: int | None = 365,
    delete_old_versions_after_days: int | None = 90,
    delete_snapshots_after_days: int | None = 90,
) -> dict:
    """段階的に低コストな層へ移し、最後に削除するルールを返す。

    Args:
        rule_name: ルール名。アカウント内で一意
        prefix_match: 対象を絞るプレフィックス。空なら全 Blob
        days_to_cool: 最終更新からこの日数でクール層へ。None で移行しない
        days_to_archive: 最終更新からこの日数でアーカイブ層へ。None で移行しない
        days_to_delete: 最終更新からこの日数で削除。None で削除しない
        delete_old_versions_after_days: 旧版を作成からこの日数で削除。None で残す
        delete_snapshots_after_days: スナップショットを作成からこの日数で削除。None で残す

    Returns:
        ManagementPolicy の properties（policy.rules を持つ dict）

    Raises:
        ValueError: ルール名が空、日数が 1 未満、
            クール → アーカイブ → 削除の順序が逆転している場合
    """
    if not rule_name:
        raise ValueError("rule_name は空にできない")

    stages = [
        ("days_to_cool", days_to_cool),
        ("days_to_archive", days_to_archive),
        ("days_to_delete", days_to_delete),
        ("delete_old_versions_after_days", delete_old_versions_after_days),
        ("delete_snapshots_after_days", delete_snapshots_after_days),
    ]
    for label, days in stages:
        if days is not None and days < 1:
            raise ValueError(f"{label} は 1 日以上: {days}")

    ordered = [(label, days) for label, days in stages[:3] if days is not None]
    for (prev_label, prev_days), (next_label, next_days) in zip(ordered, ordered[1:]):
        if prev_days >= next_days:
            raise ValueError(
                f"{prev_label} は {next_label} より小さくする: {prev_days} >= {next_days}"
            )

    base_blob: dict = {}
    if days_to_cool is not None:
        base_blob["tierToCool"] = {"daysAfterModificationGreaterThan": days_to_cool}
    if days_to_archive is not None:
        base_blob["tierToArchive"] = {
            "daysAfterModificationGreaterThan": days_to_archive
        }
    if days_to_delete is not None:
        base_blob["delete"] = {"daysAfterModificationGreaterThan": days_to_delete}

    actions: dict = {}
    if base_blob:
        actions["baseBlob"] = base_blob
    if delete_old_versions_after_days is not None:
        actions["version"] = {
            "delete": {"daysAfterCreationGreaterThan": delete_old_versions_after_days}
        }
    if delete_snapshots_after_days is not None:
        actions["snapshot"] = {
            "delete": {"daysAfterCreationGreaterThan": delete_snapshots_after_days}
        }
    if not actions:
        raise ValueError("移行も削除も指定されていない")

    return {
        "policy": {
            "rules": [
                {
                    "enabled": True,
                    "name": rule_name,
                    "type": "Lifecycle",
                    "definition": {
                        "filters": {
                            "blobTypes": ["blockBlob"],
                            "prefixMatch": list(prefix_match),
                        },
                        "actions": actions,
                    },
                }
            ]
        }
    }
