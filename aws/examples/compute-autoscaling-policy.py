"""負荷に応じて ECS サービスのタスク数を自動調整する設定を組み立てる純粋関数。

出力は boto3 ``application-autoscaling`` クライアントの ``register_scalable_target`` /
``put_scaling_policy`` の kwargs。API は呼ばない。
"""

from __future__ import annotations

_NAMESPACE = "ecs"
_DIMENSION = "ecs:service:DesiredCount"
_METRIC = "ECSServiceAverageCPUUtilization"


def ecs_target_tracking(
    cluster: str,
    service: str,
    min_capacity: int,
    max_capacity: int,
    target_cpu_percent: float,
    scale_in_cooldown: int = 300,
    scale_out_cooldown: int = 60,
) -> dict:
    """ECS サービスの CPU 使用率ターゲット追跡スケーリングの boto3 kwargs を返す。

    - ``register_scalable_target``: DesiredCount を min〜max の範囲でスケール対象にする
    - ``put_scaling_policy``: ``ECSServiceAverageCPUUtilization`` を target に保つ TargetTrackingScaling
    """
    if not cluster or not service:
        raise ValueError("cluster と service は空にできない")
    if min_capacity < 0:
        raise ValueError(f"min_capacity は 0 以上: {min_capacity}")
    if max_capacity < 1:
        raise ValueError(f"max_capacity は 1 以上: {max_capacity}")
    if min_capacity > max_capacity:
        raise ValueError(f"min_capacity <= max_capacity にする: {min_capacity} > {max_capacity}")
    if not 0 < target_cpu_percent <= 100:
        raise ValueError(f"target_cpu_percent は 0 より大きく 100 以下: {target_cpu_percent}")
    if scale_in_cooldown < 0 or scale_out_cooldown < 0:
        raise ValueError("cooldown は 0 以上の秒数")

    resource_id = f"service/{cluster}/{service}"
    return {
        "register_scalable_target": {
            "ServiceNamespace": _NAMESPACE,
            "ResourceId": resource_id,
            "ScalableDimension": _DIMENSION,
            "MinCapacity": min_capacity,
            "MaxCapacity": max_capacity,
        },
        "put_scaling_policy": {
            "PolicyName": f"{service}-cpu-target-tracking",
            "ServiceNamespace": _NAMESPACE,
            "ResourceId": resource_id,
            "ScalableDimension": _DIMENSION,
            "PolicyType": "TargetTrackingScaling",
            "TargetTrackingScalingPolicyConfiguration": {
                "TargetValue": float(target_cpu_percent),
                "PredefinedMetricSpecification": {"PredefinedMetricType": _METRIC},
                "ScaleInCooldown": scale_in_cooldown,
                "ScaleOutCooldown": scale_out_cooldown,
                "DisableScaleIn": False,
            },
        },
    }
