"""カード compute-autoscaling-policy の Contract を検証するテスト"""

import importlib
import json

import pytest

mod = importlib.import_module("compute-autoscaling-policy")
ecs_target_tracking = mod.ecs_target_tracking


def test_snapshot():
    """出力の形（boto3 kwargs）"""
    out = ecs_target_tracking("app-cluster", "api", 2, 10, 60)
    assert out == {
        "register_scalable_target": {
            "ServiceNamespace": "ecs",
            "ResourceId": "service/app-cluster/api",
            "ScalableDimension": "ecs:service:DesiredCount",
            "MinCapacity": 2,
            "MaxCapacity": 10,
        },
        "put_scaling_policy": {
            "PolicyName": "api-cpu-target-tracking",
            "ServiceNamespace": "ecs",
            "ResourceId": "service/app-cluster/api",
            "ScalableDimension": "ecs:service:DesiredCount",
            "PolicyType": "TargetTrackingScaling",
            "TargetTrackingScalingPolicyConfiguration": {
                "TargetValue": 60.0,
                "PredefinedMetricSpecification": {"PredefinedMetricType": "ECSServiceAverageCPUUtilization"},
                "ScaleInCooldown": 300,
                "ScaleOutCooldown": 60,
                "DisableScaleIn": False,
            },
        },
    }
    json.dumps(out)


def test_resource_id_and_dimension_match_between_target_and_policy():
    """ResourceId / ScalableDimension / ServiceNamespace が両 API で一致する"""
    out = ecs_target_tracking("c", "s", 1, 3, 50)
    target, policy = out["register_scalable_target"], out["put_scaling_policy"]
    for key in ("ServiceNamespace", "ResourceId", "ScalableDimension"):
        assert target[key] == policy[key]


def test_cooldown_defaults_and_override():
    """scale-in 300 秒 / scale-out 60 秒が既定。上書きできる"""
    cfg = ecs_target_tracking("c", "s", 1, 3, 50, scale_in_cooldown=600, scale_out_cooldown=0)[
        "put_scaling_policy"
    ]["TargetTrackingScalingPolicyConfiguration"]
    assert cfg["ScaleInCooldown"] == 600 and cfg["ScaleOutCooldown"] == 0


def test_min_max_boundaries():
    """min == max と min 0 は許可、min > max と max 0 は ValueError"""
    assert ecs_target_tracking("c", "s", 3, 3, 50)["register_scalable_target"]["MinCapacity"] == 3
    assert ecs_target_tracking("c", "s", 0, 1, 50)["register_scalable_target"]["MinCapacity"] == 0
    with pytest.raises(ValueError):
        ecs_target_tracking("c", "s", 5, 3, 50)
    with pytest.raises(ValueError):
        ecs_target_tracking("c", "s", 0, 0, 50)
    with pytest.raises(ValueError):
        ecs_target_tracking("c", "s", -1, 3, 50)


@pytest.mark.parametrize("target", [0, -1, 100.5, 101])
def test_target_out_of_range_rejected(target):
    """target は 0 より大きく 100 以下"""
    with pytest.raises(ValueError):
        ecs_target_tracking("c", "s", 1, 3, target)
    assert (
        ecs_target_tracking("c", "s", 1, 3, 100)["put_scaling_policy"]["TargetTrackingScalingPolicyConfiguration"][
            "TargetValue"
        ]
        == 100.0
    )


def test_negative_cooldown_and_empty_names_rejected():
    """負の cooldown・空の cluster / service は ValueError"""
    with pytest.raises(ValueError):
        ecs_target_tracking("c", "s", 1, 3, 50, scale_in_cooldown=-1)
    with pytest.raises(ValueError):
        ecs_target_tracking("c", "s", 1, 3, 50, scale_out_cooldown=-1)
    with pytest.raises(ValueError):
        ecs_target_tracking("", "s", 1, 3, 50)
    with pytest.raises(ValueError):
        ecs_target_tracking("c", "", 1, 3, 50)


def test_is_deterministic():
    """同じ入力から同じ出力"""
    assert ecs_target_tracking("c", "s", 1, 3, 50) == ecs_target_tracking("c", "s", 1, 3, 50)
