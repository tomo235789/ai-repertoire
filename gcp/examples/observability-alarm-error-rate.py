"""カード observability-alarm-error-rate: エラー率のアラートポリシーを組み立てる純粋関数。

Cloud Monitoring の `alertPolicies.create` に渡す AlertPolicy を返す。
MQL / PromQL のクエリは組み立てるだけで実行しない。API も呼ばない。
"""

from __future__ import annotations

_ALIGNMENT_SECONDS = (60, 300, 600, 900, 1800, 3600)
_COMBINERS = ("OR", "AND", "AND_WITH_MATCHING_RESOURCE")


def error_rate_alert(
    display_name: str,
    service_name: str,
    notification_channels: tuple[str, ...] | list[str],
    *,
    threshold_ratio: float = 0.05,
    alignment_seconds: int = 300,
    duration_seconds: int = 300,
    min_requests_per_interval: int = 20,
    auto_close_seconds: int = 86400,
    combiner: str = "OR",
) -> dict:
    """失敗した要求の割合がしきい値を超え続けたら発報するポリシーを返す。

    Args:
        display_name: ポリシーの表示名
        service_name: 監視対象の Cloud Run サービス名
        notification_channels: 通知チャネルの完全名。1 件以上
        threshold_ratio: 発報するエラー率。0 より大きく 1.0 以下
        alignment_seconds: 集計の刻み。_ALIGNMENT_SECONDS のいずれか
        duration_seconds: この時間だけ超え続けたら発報する
        min_requests_per_interval: この件数に満たない刻みは評価しない
        auto_close_seconds: 回復が確認できないときに自動で閉じるまでの時間
        combiner: 条件の組み合わせ方

    Returns:
        alertPolicies.create に渡せる AlertPolicy dict

    Raises:
        ValueError: 表示名やサービス名が空、通知チャネルが空、
            しきい値や刻みや件数が範囲外、未知の combiner の場合
    """
    if not display_name:
        raise ValueError("display_name は空にできない")
    if not service_name:
        raise ValueError("service_name は空にできない")
    channels = tuple(notification_channels)
    if not channels:
        raise ValueError("notification_channels は 1 件以上必要。発報しても誰も気付かない")
    if not 0 < threshold_ratio <= 1.0:
        raise ValueError(f"しきい値は 0 より大きく 1.0 以下: {threshold_ratio}")
    if alignment_seconds not in _ALIGNMENT_SECONDS:
        raise ValueError(f"集計の刻みは {_ALIGNMENT_SECONDS} のいずれか: {alignment_seconds}")
    if duration_seconds < alignment_seconds:
        raise ValueError(
            f"継続時間は集計の刻み以上にする: {duration_seconds} < {alignment_seconds}"
        )
    if duration_seconds % 60:
        raise ValueError(f"継続時間は 60 秒の倍数にする: {duration_seconds}")
    if min_requests_per_interval < 1:
        raise ValueError(f"最小件数は 1 以上: {min_requests_per_interval}")
    if combiner not in _COMBINERS:
        raise ValueError(f"combiner は {_COMBINERS} のいずれか: {combiner!r}")

    # align rate() は毎秒の値になり件数と比べられないので delta() で区間の件数を数える。
    # 件数が少ない刻みを落としてから割合を出す（1 件の失敗で 100% にしない）
    query = "\n".join(
        [
            "fetch cloud_run_revision",
            "| metric 'run.googleapis.com/request_count'",
            f"| filter resource.service_name == '{service_name}'",
            f"| align delta({alignment_seconds}s)",
            "| group_by [],"
            " [total: sum(value.request_count),"
            " failed: sum(if(metric.response_code_class == '5xx', value.request_count, 0))]",
            f"| filter total >= {min_requests_per_interval}",
            "| value [error_ratio: failed / total]",
            f"| every {alignment_seconds}s",
            f"| condition error_ratio > {threshold_ratio}",
        ]
    )

    return {
        "display_name": display_name,
        "combiner": combiner,
        "enabled": True,
        "notification_channels": sorted(set(channels)),
        "conditions": [
            {
                "display_name": f"{service_name} のエラー率が {threshold_ratio:.0%} を超えた",
                "condition_monitoring_query_language": {
                    "query": query,
                    "duration": f"{duration_seconds}s",
                },
            }
        ],
        "alert_strategy": {
            "auto_close": f"{auto_close_seconds}s",
            # 再通知の間隔はチャネルごとに決める。
            # notification_rate_limit はログベースの条件でしか効かない
            "notification_channel_strategy": [
                {
                    "notification_channel_names": sorted(set(channels)),
                    "renotify_interval": f"{max(alignment_seconds, 1800)}s",
                }
            ],
        },
        "documentation": {
            "content": (
                f"{service_name} の 5xx 応答の割合が {threshold_ratio:.0%} を "
                f"{duration_seconds} 秒間超えた。"
                f"1 刻みあたり {min_requests_per_interval} 件未満のときは評価しない。"
            ),
            "mime_type": "text/markdown",
        },
    }
