---
id: iam-least-privilege-role
lang: terraform
title: 特定の操作だけを許可する最小権限のロールを作る
tags: [最小権限, IAM ロール, サービスロール, ワイルドカード禁止, least-privilege, iam-role, permissions-boundary]
lib: hashicorp/aws
fn: aws_iam_role
since: "5.0"
verified: 2026-09-18
status: public
---

「この Lambda にはこのバケットの読み取りだけ許したい」という要求に対する設定。信頼するサービスと許可する action / resource を明示し、`*` は variable の validation で弾く。

## Signature

```hcl
module "x" { source = "./modules/iam-least-privilege-role", name, trusted_service, allowed_actions, resource_arns,
             permissions_boundary_arn = null, max_session_duration = 3600, tags = {} }
-> { role_arn, role_name, policy_name }
```

## Usage

```hcl
module "reader_role" {
  source          = "./modules/iam-least-privilege-role"
  name            = "example-reader"
  trusted_service = "lambda.amazonaws.com"
  allowed_actions = ["s3:GetObject", "s3:ListBucket"]
  resource_arns   = [module.logs.bucket_arn, "${module.logs.bucket_arn}/*"]
  tags            = { env = "prod" }
}
```

## Contract

- 信頼ポリシーは `trusted_service` からの `sts:AssumeRole` を許可する 1 文だけ。アカウントやユーザーは信頼しない
- 許可ポリシーは `Allow` 1 文で、`Action` は `allowed_actions`、`Resource` は `resource_arns` とそのまま一致する。`Deny` 文は含まない
- 弾く入力: `Action` の `*` と `<service>:*`（`s3:Get*` のような接頭辞は可）、`Resource` の `*` 単独と `arn:` で始まらない値（`arn:aws:s3:::bucket/*` のような ARN 内のワイルドカードは可）、`<service>.amazonaws.com` 形式でない principal、3600〜43200 秒の範囲外のセッション時間
- 権限はインラインポリシー（`aws_iam_role_policy`）で、ロールと同時に消える。他のロールから参照されない
- `permissions_boundary_arn` を渡すと境界が付く。既定は `null`（境界なし）。`max_session_duration` の既定は 3600
- `tags` はロールに付く（インラインポリシーはタグを持たない）
- 冪等。`name` を変えるとロールは再作成され、利用側（Lambda など）の参照 ARN も変わる

## Alternatives

- 複数ロールで同じ権限を共有するなら顧客管理ポリシー（`iam-read-only-policy` の形）を作って attach する。インラインは「このロール専用」の意味
- 引き受け元が OIDC（GitHub Actions・EKS）やクロスアカウントのときは `iam-service-identity` / `iam-cross-account-trust`。このカードはサービス principal 専用
- `Describe*` / `List*` など resource-level 権限が無いアクションを含む読み取り専用は `iam-read-only-policy`（`Resource: "*"` を受け付ける）

## Pitfalls

- IAM は「明示 Deny > 明示 Allow > 暗黙 Deny」で評価する。permissions boundary / SCP / リソースポリシーのどれかが許可しなければ、このロールが Allow していてもアクセスは通らない
- `s3:ListBucket` はバケット ARN、`s3:GetObject` はオブジェクト ARN（`/*`）が対象。片方だけ渡すと `AccessDenied` になる典型例
- ロール名はアカウント内で一意（64 文字まで）。パス（`/service/`）を分けても同名は作れない
- GCP の IAM は「ロール = 権限の束」を principal に bind する構造で、AWS の「ロール = 引き受けられる ID」とは意味が違う。GCP の対応物はサービスアカウント + カスタムロール
- ポリシーの反映は最終的整合。作成直後に Lambda が `AccessDenied` を返しても数秒で通る

## Test

`modules/iam-least-privilege-role/tests/iam-least-privilege-role.tftest.hcl`
