"""カード observability-alarm-error-rate: エラー数 / リクエスト数 の割合（%）でしきい値を判定するアラーム

cloudwatch.put_metric_alarm の kwargs を返す。メトリクス数式 `errors / requests * 100` で割合を計算する。
"""

from __future__ import annotations

import re
from typing import Any, Mapping, Sequence

_ARN_RE = re.compile(r"^arn:aws(?:-[a-z]+)?:[a-z0-9-]+:[a-z0-9-]*:\d{12}:.+$")

ALLOWED_PERIODS_UNDER_MINUTE = (10, 30)
ERROR_RATE_EXPRESSION = "errors / requests * 100"


def _check_actions(arns: Sequence[str], label: str) -> list[str]:
    items = list(arns)
    if len(set(items)) != len(items):
        raise ValueError(f"{label} に重複がある")
    for arn in items:
        if not _ARN_RE.match(arn):
            raise ValueError(f"{label}: ARN ではない: {arn!r}")
    return items


def error_rate_alarm(
    name: str,
    namespace: str,
    errors_metric: str,
    requests_metric: str,
    dimensions: Mapping[str, str],
    threshold_percent: float,
    period: int = 60,
    evaluation_periods: int = 5,
    alarm_actions: Sequence[str] = (),
    *,
    ok_actions: Sequence[str] = (),
    datapoints_to_alarm: int | None = None,
    description: str | None = None,
) -> dict[str, Any]:
    """put_metric_alarm の kwargs を返す。

    :param name: アラーム名
    :param namespace: エラー数・リクエスト数の両メトリクスの名前空間
    :param errors_metric: エラー数メトリクス名（Sum で集計）
    :param requests_metric: リクエスト数メトリクス名（Sum で集計）
    :param dimensions: 両メトリクスに共通のディメンション（{"Name": "Value"}）
    :param threshold_percent: この % を超えたら ALARM（0〜100）
    :param period: 集計期間秒。10 / 30 か 60 の倍数
    :param evaluation_periods: 評価する期間数
    :param alarm_actions: ALARM 時に通知する SNS トピックなどの ARN
    :param datapoints_to_alarm: N 個中 M 個で発報の M。None なら evaluation_periods と同じ
    """
    if not name or len(name) > 255:
        raise ValueError(f"アラーム名は 1〜255 文字: {name!r}")
    if not namespace:
        raise ValueError("namespace は必須")
    if not errors_metric or not requests_metric:
        raise ValueError("errors_metric と requests_metric は必須")
    if isinstance(threshold_percent, bool) or not isinstance(threshold_percent, (int, float)):
        raise TypeError("threshold_percent は数値")
    if not 0 <= threshold_percent <= 100:
        raise ValueError(f"threshold_percent は 0〜100（実際: {threshold_percent}）")
    if isinstance(period, bool) or not isinstance(period, int) or period <= 0:
        raise ValueError(f"period は正の int（実際: {period!r}）")
    if period not in ALLOWED_PERIODS_UNDER_MINUTE and period % 60 != 0:
        raise ValueError(f"period は 10、30 か 60 の倍数（実際: {period}）")
    if isinstance(evaluation_periods, bool) or not isinstance(evaluation_periods, int) or evaluation_periods < 1:
        raise ValueError(f"evaluation_periods は 1 以上の int（実際: {evaluation_periods!r}）")
    if datapoints_to_alarm is None:
        datapoints_to_alarm = evaluation_periods
    if isinstance(datapoints_to_alarm, bool) or not 1 <= datapoints_to_alarm <= evaluation_periods:
        raise ValueError(f"datapoints_to_alarm は 1〜evaluation_periods（実際: {datapoints_to_alarm!r}）")
    alarm_arns = _check_actions(alarm_actions, "alarm_actions")
    ok_arns = _check_actions(ok_actions, "ok_actions")

    dims = [{"Name": k, "Value": v} for k, v in dimensions.items()]

    def metric_stat(metric_name: str) -> dict[str, Any]:
        return {
            "Metric": {"Namespace": namespace, "MetricName": metric_name, "Dimensions": dims},
            "Period": period,
            "Stat": "Sum",
        }

    return {
        "AlarmName": name,
        "AlarmDescription": description or f"{errors_metric} / {requests_metric} が {threshold_percent}% を超えた",
        "ActionsEnabled": True,
        "AlarmActions": alarm_arns,
        "OKActions": ok_arns,
        "Metrics": [
            {"Id": "errors", "MetricStat": metric_stat(errors_metric), "ReturnData": False},
            {"Id": "requests", "MetricStat": metric_stat(requests_metric), "ReturnData": False},
            {"Id": "error_rate", "Expression": ERROR_RATE_EXPRESSION, "Label": "Error rate (%)", "ReturnData": True},
        ],
        "ComparisonOperator": "GreaterThanThreshold",
        "Threshold": float(threshold_percent),
        "EvaluationPeriods": evaluation_periods,
        "DatapointsToAlarm": datapoints_to_alarm,
        "TreatMissingData": "notBreaching",
    }
