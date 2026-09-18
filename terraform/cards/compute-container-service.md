---
id: compute-container-service
lang: terraform
title: コンテナを常駐サービスとして実行する
tags: [コンテナ, 常駐サービス, Fargate, ecs-service, fargate, task-definition, awslogs]
lib: hashicorp/aws
fn: aws_ecs_service
since: "5.0"
verified: 2026-09-18
status: public
---

Fargate のタスク定義と ECS サービスを作る。タスクはプライベートサブネットに置いてパブリック IP を付けず、ログは保持期間付きの CloudWatch ロググループへ送る。

## Signature

```hcl
variables: name, cluster, image, cpu = 256, memory = 512, desired_count = 2, container_port = 8080, subnet_ids, security_group_ids, execution_role_arn, task_role_arn = null, environment = {}, region, log_retention_days = 30, tags = {}
outputs:   service_id, service_name, task_definition_arn, log_group_name
```

## Usage

```hcl
module "app" {
  source             = "./modules/compute-container-service"
  name               = "app"
  cluster            = "arn:aws:ecs:us-east-1:123456789012:cluster/example"
  image              = "123456789012.dkr.ecr.us-east-1.amazonaws.com/app:1.2.3"
  subnet_ids         = [module.private_a.subnet_id]
  security_group_ids = [module.web_sg.security_group_id]
  execution_role_arn = "arn:aws:iam::123456789012:role/app-execution"
  region             = "us-east-1"
}
```

## Contract

- `launch_type = "FARGATE"`、`network_mode = "awsvpc"`、`assign_public_ip = false`。タスクにパブリック IP は付かない
- コンテナのログは `awslogs` ドライバで `/ecs/<name>` に送る。ロググループは `log_retention_days`（既定 30 日）付きで module が作る
- 実行ロール（`execution_role_arn`）は必須、タスクロール（`task_role_arn`）は任意。アプリが AWS API を呼ばないなら `null` でよい
- `environment` は `name` / `value` の配列としてコンテナ定義に入る
- デプロイ失敗時はサーキットブレーカーで前のタスク定義へ自動ロールバック
- `cpu` は Fargate が受け付ける値（256〜16384）、`memory` は 512 か 1024 の倍数、`desired_count` は 0 以上、`log_retention_days` は CloudWatch の許可値のみ。それ以外は validation で拒否
- `tags` をロググループ・タスク定義・サービスに付け、サービスのタグをタスクにも伝播する

## Alternatives

- HTTP を受けるサービスは ALB のターゲットグループに登録する。この module は `load_balancer` ブロックを持たないので、必要なら `aws_ecs_service` を直接書く
- 負荷に応じてタスク数を変えるなら compute-autoscaling-policy に `service_name` を渡す
- 秘密情報は `environment` に入れず、secret-fetch-at-runtime（Secrets Manager 参照）を使う
- 短時間で終わる処理はサービスではなく compute-serverless-function かスケジュールタスク

## Pitfalls

- `name`（family）や `cluster` の変更はサービスの再作成になる。タスク定義は変更のたびに新しいリビジョンが作られ、旧リビジョンは残る
- `cpu` / `memory` の組み合わせは Fargate の対応表に従う（例 256 CPU なら 512〜2048 MB）。validation は個々の値しか見ないので、組み合わせ違いは apply で失敗する
- `image` のタグを `latest` にすると plan では差分が出ず、デプロイのタイミングでイメージが変わる。タグかダイジェストで固定する
- プライベートサブネットからイメージ取得とログ送信をするには、NAT（network-egress-only）か ECR / CloudWatch Logs / S3 の VPC エンドポイント（network-private-endpoint）が要る

## Test

`modules/compute-container-service/tests/compute-container-service.tftest.hcl`
