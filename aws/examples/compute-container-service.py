"""コンテナを常駐サービスとして実行する ECS Fargate の設定を組み立てる純粋関数。

出力は boto3 ``ecs`` クライアントの ``register_task_definition`` / ``create_service`` の kwargs。API は呼ばない。
"""

from __future__ import annotations

# Fargate (Linux) の CPU 単位 → 許容メモリ (MiB) の範囲と刻み
_FARGATE_MEMORY: dict[int, range] = {
    256: range(512, 2048 + 1, 512),
    512: range(1024, 4096 + 1, 1024),
    1024: range(2048, 8192 + 1, 1024),
    2048: range(4096, 16384 + 1, 1024),
    4096: range(8192, 30720 + 1, 1024),
    8192: range(16384, 61440 + 1, 4096),
    16384: range(32768, 122880 + 1, 8192),
}


def _validate_cpu_memory(cpu: int, memory: int) -> None:
    allowed = _FARGATE_MEMORY.get(cpu)
    if allowed is None:
        raise ValueError(f"cpu は Fargate の許容値 {sorted(_FARGATE_MEMORY)} のいずれか: {cpu}")
    if memory not in allowed:
        raise ValueError(
            f"cpu={cpu} のとき memory は {allowed.start}〜{allowed.stop - 1} MiB を {allowed.step} 刻み: {memory}"
        )


def _validate_image(image: str) -> None:
    name = image.rsplit("/", 1)[-1]
    if "@sha256:" in name:
        return
    if ":" not in name or name.endswith(":latest"):
        raise ValueError(f"image はタグかダイジェストで固定する（latest 不可）: {image}")


def fargate_service(
    cluster: str,
    name: str,
    image: str,
    cpu: int,
    memory: int,
    subnets: list[str],
    security_groups: list[str],
    execution_role_arn: str,
    task_role_arn: str,
    log_group: str,
    *,
    region: str,
    container_port: int | None = None,
    desired_count: int = 1,
    env: dict[str, str] | None = None,
) -> dict:
    """Fargate 常駐サービス 1 つ分の boto3 kwargs を返す。

    - ``register_task_definition``: awsvpc / FARGATE、awslogs でログ出力
    - ``create_service``: プライベートサブネットに配置し ``assignPublicIp`` は ``DISABLED``
    """
    if not cluster or not name:
        raise ValueError("cluster と name は空にできない")
    _validate_image(image)
    _validate_cpu_memory(cpu, memory)
    if not subnets or any(not s.startswith("subnet-") for s in subnets):
        raise ValueError(f"subnets は subnet-xxxx を 1 つ以上: {subnets}")
    if not security_groups or any(not s.startswith("sg-") for s in security_groups):
        raise ValueError(f"security_groups は sg-xxxx を 1 つ以上: {security_groups}")
    for label, arn in (("execution_role_arn", execution_role_arn), ("task_role_arn", task_role_arn)):
        if not arn.startswith("arn:aws:iam::"):
            raise ValueError(f"{label} は IAM ロールの ARN: {arn}")
    if not log_group or not region:
        raise ValueError("log_group と region は空にできない")
    if container_port is not None and not 1 <= container_port <= 65535:
        raise ValueError(f"container_port は 1〜65535: {container_port}")
    if desired_count < 0:
        raise ValueError(f"desired_count は 0 以上: {desired_count}")

    container: dict = {
        "name": name,
        "image": image,
        "essential": True,
        "readonlyRootFilesystem": True,
        "logConfiguration": {
            "logDriver": "awslogs",
            "options": {
                "awslogs-group": log_group,
                "awslogs-region": region,
                "awslogs-stream-prefix": name,
            },
        },
    }
    if container_port is not None:
        container["portMappings"] = [{"containerPort": container_port, "protocol": "tcp"}]
    if env:
        container["environment"] = [{"name": k, "value": v} for k, v in env.items()]

    return {
        "register_task_definition": {
            "family": name,
            "networkMode": "awsvpc",
            "requiresCompatibilities": ["FARGATE"],
            "cpu": str(cpu),
            "memory": str(memory),
            "executionRoleArn": execution_role_arn,
            "taskRoleArn": task_role_arn,
            "containerDefinitions": [container],
        },
        "create_service": {
            "cluster": cluster,
            "serviceName": name,
            "taskDefinition": name,
            "launchType": "FARGATE",
            "desiredCount": desired_count,
            "networkConfiguration": {
                "awsvpcConfiguration": {
                    "subnets": list(subnets),
                    "securityGroups": list(security_groups),
                    "assignPublicIp": "DISABLED",
                }
            },
            "enableExecuteCommand": False,
            "propagateTags": "SERVICE",
        },
    }
