"""カード database-backup-retention: バックアップと保持期間の設定を組み立てる純粋関数。

`azure-mgmt-rdbms` のサーバー更新に渡す backup プロパティと、
長期保持ポリシーの設定を返す。API は呼ばない。
"""

from __future__ import annotations

# 自動バックアップの保持日数の範囲
MIN_RETENTION_DAYS = 7
MAX_RETENTION_DAYS = 35
# 長期保持は週次・月次・年次を ISO 8601 の duration で指定する
MAX_WEEKLY_WEEKS = 520
MAX_MONTHLY_MONTHS = 120
MAX_YEARLY_YEARS = 10


def backup_retention_config(
    *,
    retention_days: int = 35,
    geo_redundant: bool = True,
    weekly_retention_weeks: int | None = None,
    monthly_retention_months: int | None = None,
    yearly_retention_years: int | None = None,
    week_of_year_for_yearly: int = 1,
) -> dict:
    """自動バックアップと長期保持の設定を返す。

    Args:
        retention_days: 自動バックアップの保持日数。7〜35
        geo_redundant: ペアリージョンへバックアップを複製するか
        weekly_retention_weeks: 週次バックアップの保持週数。None で使わない
        monthly_retention_months: 月次バックアップの保持月数。None で使わない
        yearly_retention_years: 年次バックアップの保持年数。None で使わない
        week_of_year_for_yearly: 年次として残す週の番号。1〜52

    Returns:
        backup と long_term_retention を持つ dict

    Raises:
        ValueError: 保持日数が 7〜35 の外、長期保持の値が範囲外、
            年次だけを指定して週番号が範囲外、長期保持が自動バックアップより短い場合
    """
    if not MIN_RETENTION_DAYS <= retention_days <= MAX_RETENTION_DAYS:
        raise ValueError(
            f"保持日数は {MIN_RETENTION_DAYS}〜{MAX_RETENTION_DAYS} 日: {retention_days}"
        )
    if not 1 <= week_of_year_for_yearly <= 52:
        raise ValueError(f"年次として残す週は 1〜52: {week_of_year_for_yearly}")

    for label, value, upper in (
        ("weekly_retention_weeks", weekly_retention_weeks, MAX_WEEKLY_WEEKS),
        ("monthly_retention_months", monthly_retention_months, MAX_MONTHLY_MONTHS),
        ("yearly_retention_years", yearly_retention_years, MAX_YEARLY_YEARS),
    ):
        if value is not None and not 1 <= value <= upper:
            raise ValueError(f"{label} は 1〜{upper}: {value}")

    if weekly_retention_weeks is not None and weekly_retention_weeks * 7 <= retention_days:
        raise ValueError(
            "週次の長期保持は自動バックアップの保持期間より長くする: "
            f"{weekly_retention_weeks * 7} <= {retention_days}"
        )

    long_term_retention: dict = {
        "weeklyRetention": f"P{weekly_retention_weeks}W" if weekly_retention_weeks else "PT0S",
        "monthlyRetention": (
            f"P{monthly_retention_months}M" if monthly_retention_months else "PT0S"
        ),
        "yearlyRetention": f"P{yearly_retention_years}Y" if yearly_retention_years else "PT0S",
        "weekOfYear": week_of_year_for_yearly if yearly_retention_years else 0,
    }

    return {
        "backup": {
            "backupRetentionDays": retention_days,
            "geoRedundantBackup": "Enabled" if geo_redundant else "Disabled",
        },
        "long_term_retention": long_term_retention,
    }
