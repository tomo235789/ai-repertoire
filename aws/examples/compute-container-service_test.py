"""カード compute-container-service の Contract を検証するテスト"""

import importlib
import json

import pytest

mod = importlib.import_module("compute-container-service")
fargate_service = mod.fargate_service

ARGS = dict(
    cluster="app-cluster",
    name="api",
    image="123456789012.dkr.ecr.us-east-1.amazonaws.com/api:1.2.3",
    cpu=256,
    memory=512,
    subnets=["subnet-0a", "subnet-0b"],
    security_groups=["sg-0abc"],
    execution_role_arn="arn:aws:iam::123456789012:role/api-exec",
    task_role_arn="arn:aws:iam::123456789012:role/api-task",
    log_group="/ecs/api",
    region="us-east-1",
)


def test_snapshot():
    """出力の形（boto3 kwargs）"""
    out = fargate_service(**ARGS, container_port=8080)
    assert out == {
        "register_task_definition": {
            "family": "api",
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": "256",
            "memory": "512",
            "executionRoleArn": "arn:aws:iam::123456789012:role/api-exec",
            "taskRoleArn": "arn:aws:iam::123456789012:role/api-task",
            "containerDefinitions": [
                {
                    "name": "api",
                    "image": "123456789012.dkr.ecr.us-east-1.amazonaws.com/api:1.2.3",
                    "essential": True,
                    "readonlyRootFilesystem": True,
                    "logConfiguration": {
                        "logDriver": "awslogs",
                        "options": {
                            "awslogs-group": "/ecs/api",
                            "awslogs-region": "us-east-1",
                            "awslogs-stream-prefix": "api",
                        },
                    },
                    "portMappings": [{"containerPort": 8080, "protocol": "tcp"}],
                }
            ],
        },
        "create_service": {
            "cluster": "app-cluster",
            "serviceName": "api",
            "taskDefinition": "api",
            "launchType": "FARGATE",
            "desiredCount": 1,
            "networkConfiguration": {
                "awsvpcConfiguration": {
                    "subnets": ["subnet-0a", "subnet-0b"],
                    "securityGroups": ["sg-0abc"],
                    "assignPublicIp": "DISABLED",
                }
            },
            "enableExecuteCommand": False,
            "propagateTags": "SERVICE",
        },
    }
    json.dumps(out)


def test_no_public_ip_and_no_exec():
    """パブリック IP を付けず、ECS Exec も無効"""
    svc = fargate_service(**ARGS)["create_service"]
    assert svc["networkConfiguration"]["awsvpcConfiguration"]["assignPublicIp"] == "DISABLED"
    assert svc["enableExecuteCommand"] is False


def test_optional_port_and_env_omitted_by_default():
    """container_port / env を渡さなければ portMappings / environment を出さない"""
    container = fargate_service(**ARGS)["register_task_definition"]["containerDefinitions"][0]
    assert "portMappings" not in container
    assert "environment" not in container
    with_env = fargate_service(**ARGS, env={"LOG_LEVEL": "info"})
    assert with_env["register_task_definition"]["containerDefinitions"][0]["environment"] == [
        {"name": "LOG_LEVEL", "value": "info"}
    ]


@pytest.mark.parametrize(
    "cpu,memory",
    [(256, 512), (256, 2048), (512, 4096), (1024, 8192), (2048, 16384), (4096, 30720), (8192, 61440), (16384, 122880)],
)
def test_valid_fargate_combinations(cpu, memory):
    """Fargate の許容組み合わせは通り、文字列で出力される"""
    td = fargate_service(**{**ARGS, "cpu": cpu, "memory": memory})["register_task_definition"]
    assert td["cpu"] == str(cpu) and td["memory"] == str(memory)


@pytest.mark.parametrize(
    "cpu,memory",
    [(256, 4096), (256, 768), (512, 512), (1024, 1024), (2048, 3072), (8192, 17408), (128, 512), (300, 1024)],
)
def test_invalid_fargate_combinations_rejected(cpu, memory):
    """許容外の cpu / memory は ValueError"""
    with pytest.raises(ValueError):
        fargate_service(**{**ARGS, "cpu": cpu, "memory": memory})


@pytest.mark.parametrize(
    "image",
    ["123456789012.dkr.ecr.us-east-1.amazonaws.com/api", "123456789012.dkr.ecr.us-east-1.amazonaws.com/api:latest", "nginx"],
)
def test_untagged_or_latest_image_rejected(image):
    """タグ無し・latest は ValueError。ダイジェスト指定は通る"""
    with pytest.raises(ValueError):
        fargate_service(**{**ARGS, "image": image})
    digest = "123456789012.dkr.ecr.us-east-1.amazonaws.com/api@sha256:" + "a" * 64
    assert fargate_service(**{**ARGS, "image": digest})["register_task_definition"]["containerDefinitions"][0]["image"] == digest


@pytest.mark.parametrize(
    "kwargs",
    [
        {"subnets": []},
        {"subnets": ["sg-0abc"]},
        {"security_groups": []},
        {"security_groups": ["subnet-0a"]},
        {"execution_role_arn": "api-exec"},
        {"task_role_arn": "arn:aws:s3:::bucket"},
        {"log_group": ""},
        {"region": ""},
        {"name": ""},
        {"container_port": 0},
        {"desired_count": -1},
    ],
)
def test_invalid_args_rejected(kwargs):
    """ID / ARN の形式違い・空値・範囲外は ValueError"""
    with pytest.raises(ValueError):
        fargate_service(**{**ARGS, **kwargs})


def test_is_deterministic_and_copies_lists():
    """同じ入力から同じ出力。出力のリストは引数と別オブジェクト"""
    a = fargate_service(**ARGS)
    b = fargate_service(**ARGS)
    assert a == b
    assert a["create_service"]["networkConfiguration"]["awsvpcConfiguration"]["subnets"] is not ARGS["subnets"]
