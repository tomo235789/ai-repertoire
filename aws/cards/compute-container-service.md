---
id: compute-container-service
lang: aws
title: コンテナを常駐サービスとして実行する
tags: [コンテナ, 常駐, ECS, Fargate, container, service, task definition, ecs]
lib: aws.ecs
fn: fargate_service
since: "2024"
verified: 2026-09-18
status: public
---

ECS Fargate のタスク定義とサービスを組み立てる。プライベートサブネットに置き、パブリック IP を付けず、awslogs でログを出す。出力は boto3 `ecs` の `register_task_definition` / `create_service` の kwargs。

## Signature

```python
fargate_service(cluster: str, name: str, image: str, cpu: int, memory: int, subnets: list[str], security_groups: list[str], execution_role_arn: str, task_role_arn: str, log_group: str, *, region: str, container_port: int | None = None, desired_count: int = 1, env: dict[str, str] | None = None) -> dict
```

## Usage

```python
from importlib import import_module

fargate_service = import_module("compute-container-service").fargate_service
cfg = fargate_service("app-cluster", "api", "123456789012.dkr.ecr.us-east-1.amazonaws.com/api:1.2.3", 256, 512,
                      ["subnet-0a", "subnet-0b"], ["sg-0abc"], "arn:aws:iam::123456789012:role/api-exec",
                      "arn:aws:iam::123456789012:role/api-task", "/ecs/api", region="us-east-1", container_port=8080)
# cfg["register_task_definition"] -> ecs.register_task_definition(**...)  cpu/memory は "256"/"512" の文字列
# cfg["create_service"]           -> ecs.create_service(**...)            assignPublicIp は "DISABLED"
```

## Contract

- 副作用無し。同じ入力から同じ出力。出力のリストは引数と別オブジェクト。出力は `json.dumps` できる
- `create_service` は `launchType: FARGATE`、`assignPublicIp: DISABLED`、`enableExecuteCommand: False`、`propagateTags: SERVICE`
- `register_task_definition` は `networkMode: awsvpc`、`requiresCompatibilities: ["FARGATE"]`、コンテナは `essential: True`、`readonlyRootFilesystem: True`、`awslogs`（`awslogs-group` = `log_group`、`awslogs-region` = `region`、`awslogs-stream-prefix` = `name`）
- `cpu` / `memory` は Fargate (Linux) の許容組み合わせ（256: 512〜2048、512: 1024〜4096、1024: 2048〜8192、2048: 4096〜16384、4096: 8192〜30720、8192: 16384〜61440 を 4096 刻み、16384: 32768〜122880 を 8192 刻み）以外は `ValueError`。出力では文字列
- `image` はタグかダイジェスト必須。タグ無しと `:latest` は `ValueError`
- `subnets` / `security_groups` は空、または `subnet-` / `sg-` 以外の接頭辞で `ValueError`。ロール ARN は `arn:aws:iam::` 始まりでなければ `ValueError`
- `container_port` / `env` を渡さなければ `portMappings` / `environment` を出さない。`container_port` は 1〜65535、`desired_count` は 0 以上

## Alternatives

- Terraform: `terraform/modules/compute-container-service`（同じ ID。`aws_ecs_task_definition` + `aws_ecs_service`）
- CloudFormation: `AWS::ECS::TaskDefinition` + `AWS::ECS::Service`
- 常駐でなくリクエスト駆動なら App Runner、イベント駆動なら compute-serverless-function。スケーリングは compute-autoscaling-policy

## Pitfalls

- `create_service.taskDefinition` は family 名（最新 ACTIVE リビジョン）。特定リビジョンに固定するなら `register_task_definition` の応答 `taskDefinition.taskDefinitionArn` で差し替える
- ロググループは自動作成されない。`logs.create_log_group` を先に行うか `awslogs-create-group: "true"` を足す（execution role に `logs:CreateLogGroup` が要る）
- `assignPublicIp: DISABLED` のサブネットからイメージを pull するには NAT（network-egress-only）か ECR / S3 / CloudWatch Logs のエンドポイント（network-private-endpoint）が要る
- `readonlyRootFilesystem: True` で `/tmp` に書けない。必要なら `mountPoints` + `volumes` を足す
- タスク定義は不変。変更は新リビジョンの登録 + `update_service`。`family` / `networkMode` は同じ family 内で変えない
- ARM（Graviton）にするなら `runtimePlatform.cpuArchitecture: ARM64` を足す。既定は X86_64

## Test

`examples/compute-container-service_test.py`
