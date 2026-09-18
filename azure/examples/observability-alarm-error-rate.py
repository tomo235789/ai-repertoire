"""カード observability-alarm-error-rate: エラー率のアラート規則を組み立てる純粋関数。

`azure-mgmt-monitor` の `scheduled_query_rules.create_or_update` に渡す
プロパティを返す。API は呼ばず、クエリは組み立てるだけで実行しない。
"""

from __future__ import annotations

# 評価間隔と対象期間は ISO 8601 の duration で渡す
_ALLOWED_WINDOW_MINUTES = (5, 10, 15, 30, 60, 120, 180, 360, 720, 1440)
_SEVERITY_RANGE = range(0, 5)


def _iso_minutes(minutes: int) -> str:
    if minutes % 60 == 0:
        return f"PT{minutes // 60}H"
    return f"PT{minutes}M"


def error_rate_alert(
    name: str,
    scope_id: str,
    action_group_id: str,
    *,
    threshold_percent: float = 5.0,
    window_minutes: int = 15,
    evaluation_minutes: int = 5,
    min_requests: int = 20,
    severity: int = 1,
    auto_mitigate: bool = True,
) -> dict:
    """失敗した要求の割合がしきい値を超えたら発報する規則を返す。

    Args:
        name: アラート規則名
        scope_id: 監視対象リソースの ARM ID
        action_group_id: 通知先アクショングループの ARM ID
        threshold_percent: 発報するエラー率。0 より大きく 100 以下
        window_minutes: 評価に使う集計期間
        evaluation_minutes: 評価の実行間隔。集計期間以下
        min_requests: この件数に満たない期間は評価しない
        severity: 重大度。0（最重大）〜4
        auto_mitigate: 回復したら自動で解決扱いにするか

    Returns:
        ScheduledQueryRule の properties にそのまま渡せる dict

    Raises:
        ValueError: 名前が空、ARM ID の形式違い、しきい値が範囲外、
            集計期間が許可されていない、評価間隔が集計期間より長い、
            最小件数が 1 未満、重大度が 0〜4 の外の場合
    """
    if not name:
        raise ValueError("name は空にできない")
    for label, value in (("scope_id", scope_id), ("action_group_id", action_group_id)):
        if not value.startswith("/subscriptions/"):
            raise ValueError(f"{label} は ARM リソース ID を指定する: {value!r}")
    if not 0 < threshold_percent <= 100:
        raise ValueError(f"しきい値は 0 より大きく 100 以下: {threshold_percent}")
    if window_minutes not in _ALLOWED_WINDOW_MINUTES:
        raise ValueError(f"集計期間は {_ALLOWED_WINDOW_MINUTES} のいずれか: {window_minutes}")
    if evaluation_minutes not in _ALLOWED_WINDOW_MINUTES:
        raise ValueError(f"評価間隔は {_ALLOWED_WINDOW_MINUTES} のいずれか: {evaluation_minutes}")
    if evaluation_minutes > window_minutes:
        raise ValueError(
            f"評価間隔は集計期間以下にする: {evaluation_minutes} > {window_minutes}"
        )
    if min_requests < 1:
        raise ValueError(f"最小件数は 1 以上: {min_requests}")
    if severity not in _SEVERITY_RANGE:
        raise ValueError(f"重大度は 0〜4: {severity}")

    # 件数が少ないときに 1 件の失敗で 100% にならないよう、最小件数で足切りする
    query = (
        "requests"
        f"\n| where timestamp > ago({window_minutes}m)"
        "\n| summarize total = count(), failed = countif(success == false)"
        f"\n| where total >= {min_requests}"
        "\n| extend errorRate = 100.0 * failed / total"
        "\n| project errorRate"
    )

    return {
        "displayName": name,
        "severity": severity,
        "enabled": True,
        "scopes": [scope_id],
        "evaluationFrequency": _iso_minutes(evaluation_minutes),
        "windowSize": _iso_minutes(window_minutes),
        "criteria": {
            "allOf": [
                {
                    "query": query,
                    "timeAggregation": "Maximum",
                    "metricMeasureColumn": "errorRate",
                    "operator": "GreaterThan",
                    "threshold": threshold_percent,
                    "failingPeriods": {
                        "numberOfEvaluationPeriods": 1,
                        "minFailingPeriodsToAlert": 1,
                    },
                }
            ]
        },
        "actions": {"actionGroups": [action_group_id]},
        "autoMitigate": auto_mitigate,
        # データが来ないこと自体は別の規則で見る
        "checkWorkspaceAlertsStorageConfigured": False,
    }
