"""カード storage-bucket-lifecycle: バケットのライフサイクル規則を組み立てる純粋関数。

`google-cloud-storage` の `Bucket.lifecycle_rules` に渡す規則の列を返す。
API は呼ばず、現在時刻も使わない。
"""

from __future__ import annotations

# 単価が下がる順。前の階層より長い日数でしか移せない
STORAGE_CLASS_ORDER = ("STANDARD", "NEARLINE", "COLDLINE", "ARCHIVE")
# 階層ごとの最低保存期間（日）。これより早く消すと早期削除の料金がかかる
MINIMUM_STORAGE_DAYS = {"STANDARD": 0, "NEARLINE": 30, "COLDLINE": 90, "ARCHIVE": 365}


def lifecycle_rules(
    *,
    transitions: dict[str, int] | None = None,
    delete_after_days: int | None = 365,
    delete_noncurrent_after_days: int | None = 30,
    keep_newer_versions: int = 3,
    matches_prefix: tuple[str, ...] | list[str] = (),
) -> list[dict]:
    """階層の移行と削除の規則を、条件の緩い順に並べて返す。

    Args:
        transitions: 移行先クラス -> 経過日数。省略すると NEARLINE 30 日・COLDLINE 90 日
        delete_after_days: 作成からこの日数で削除。None で削除しない
        delete_noncurrent_after_days: 旧版をこの日数で削除。None で残す
        keep_newer_versions: 旧版を消すときに必ず残す新しい版の数
        matches_prefix: 対象を絞るプレフィックス

    Returns:
        `lifecycle_rules` にそのまま渡せる規則のリスト

    Raises:
        ValueError: 未知のストレージクラス、日数が 1 未満、
            移行の順序が階層の順序と逆、削除が最後の移行より早い、
            最後の階層の最低保存期間より前に削除する、残す版の数が負の場合
    """
    if transitions is None:
        transitions = {"NEARLINE": 30, "COLDLINE": 90}
    if keep_newer_versions < 0:
        raise ValueError(f"残す版の数は 0 以上: {keep_newer_versions}")

    for storage_class, days in transitions.items():
        if storage_class not in MINIMUM_STORAGE_DAYS:
            raise ValueError(f"未知のストレージクラス: {storage_class!r}")
        if storage_class == "STANDARD":
            raise ValueError("STANDARD へは移行できない")
        if days < 1:
            raise ValueError(f"移行日数は 1 以上: {storage_class}={days}")

    ordered = sorted(transitions.items(), key=lambda item: STORAGE_CLASS_ORDER.index(item[0]))
    for (prev_class, prev_days), (next_class, next_days) in zip(ordered, ordered[1:]):
        if prev_days >= next_days:
            raise ValueError(
                f"{prev_class} は {next_class} より早く移行する: {prev_days} >= {next_days}"
            )
    if delete_after_days is not None:
        if delete_after_days < 1:
            raise ValueError(f"削除日数は 1 以上: {delete_after_days}")
        if ordered and delete_after_days <= ordered[-1][1]:
            raise ValueError(
                f"削除は最後の移行より後にする: {delete_after_days} <= {ordered[-1][1]}"
            )
        # 最後の階層に移してすぐ消すと早期削除の料金がかかる
        if ordered:
            last_class, last_days = ordered[-1]
            minimum = MINIMUM_STORAGE_DAYS[last_class]
            if delete_after_days - last_days < minimum:
                raise ValueError(
                    f"{last_class} の最低保存期間は {minimum} 日。"
                    f"移行 {last_days} 日の後、削除は {last_days + minimum} 日以降にする"
                )
    if delete_noncurrent_after_days is not None and delete_noncurrent_after_days < 1:
        raise ValueError(f"旧版の削除日数は 1 以上: {delete_noncurrent_after_days}")

    prefix_condition = {"matchesPrefix": list(matches_prefix)} if matches_prefix else {}
    rules: list[dict] = [
        {
            "action": {"type": "SetStorageClass", "storageClass": storage_class},
            "condition": {"age": days, **prefix_condition},
        }
        for storage_class, days in ordered
    ]
    if delete_after_days is not None:
        rules.append(
            {
                "action": {"type": "Delete"},
                "condition": {"age": delete_after_days, **prefix_condition},
            }
        )
    if delete_noncurrent_after_days is not None:
        rules.append(
            {
                "action": {"type": "Delete"},
                "condition": {
                    "daysSinceNoncurrentTime": delete_noncurrent_after_days,
                    "numNewerVersions": keep_newer_versions,
                    **prefix_condition,
                },
            }
        )
    return rules
