---
id: iam-service-identity
lang: terraform
title: ワークロード用のサービス ID にリソースへのアクセスを与える
tags: [サービス ID, ワークロード ID, OIDC, アクセスキー不要, GitHub Actions, workload-identity, oidc, assume-role]
lib: hashicorp/aws
fn: aws_iam_role
since: "5.0"
verified: 2026-09-18
status: public
---

「ECS タスクや GitHub Actions に、アクセスキーを配らずに AWS を触らせたい」という要求に対する設定。サービス principal か OIDC プロバイダから引き受けるロールを作り、管理ポリシーを attach する。

## Signature

```hcl
module "x" { source = "./modules/iam-service-identity", name, principal_type = "service" | "oidc", service_principal = null,
             oidc_provider_arn = null, oidc_subjects = [], oidc_audiences = ["sts.amazonaws.com"], policy_arns = [], permissions_boundary_arn = null, max_session_duration = 3600, tags = {} }
-> { role_arn, role_name, assume_action }
```

## Usage

```hcl
module "deploy_identity" {
  source            = "./modules/iam-service-identity"
  name              = "example-github-deploy"
  principal_type    = "oidc"
  oidc_provider_arn = "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com"
  oidc_subjects     = ["repo:example-org/example-repo:ref:refs/heads/main"]
  policy_arns       = [module.logs_read_only.policy_arn]
}
# module.deploy_identity.role_arn を GitHub Actions の role-to-assume に渡す
```

## Contract

- IAM ユーザーも長期アクセスキーも作らない。資格情報は STS の一時トークンだけ（`assume_action` 出力が `sts:AssumeRole` か `sts:AssumeRoleWithWebIdentity`）
- `principal_type = "service"`: 信頼ポリシーは `service_principal` からの `sts:AssumeRole` 1 文だけ
- `principal_type = "oidc"`: `Federated = oidc_provider_arn` からの `sts:AssumeRoleWithWebIdentity` 1 文で、`<host>:aud` は常に `StringEquals`（既定 `sts.amazonaws.com`）、`<host>:sub` は `*` を含まなければ `StringEquals`、含めば `StringLike`。`host` は ARN の `oidc-provider/` 以降から導出する
- 弾く入力: `service` で `service_principal` 無し、`oidc` で `oidc_provider_arn` か `oidc_subjects` 無し（プロバイダの全トークンを信頼してしまう）、`service` / `oidc` 以外の `principal_type`、`oidc-provider/` でない ARN、3600〜43200 秒外のセッション時間
- `policy_arns` は `for_each` で attach され、追加・削除は他の attach に影響しない。既定は `[]`（権限なし）
- `tags` はロールに付く。`max_session_duration` の既定は 3600
- 冪等。`name` を変えるとロールは再作成され、`role_arn` も変わる

## Alternatives

- EKS の Pod なら EKS Pod Identity（`aws_eks_pod_identity_association`、principal は `pods.eks.amazonaws.com`）が OIDC（IRSA）より設定が少ない。`principal_type = "service"` で作ったロールを渡す
- ロール専用の権限をインラインで持たせたいときは `iam-least-privilege-role`。このカードは既存の管理ポリシーを attach する側
- 別 AWS アカウントからの引き受けは `iam-cross-account-trust`（ExternalId 必須）

## Pitfalls

- OIDC プロバイダ（`aws_iam_openid_connect_provider`）はアカウントに 1 URL につき 1 つ。module 内では作らず ARN を受け取る
- GitHub Actions の `sub` は `repo:<org>/<repo>:ref:refs/heads/<branch>` / `:environment:<env>` / `:pull_request` と文脈で変わる。`StringEquals` で 1 つだけ書くと PR からの実行が引き受けられない
- `sub` に `repo:org/*` のような広いパターンを書くと組織の全リポジトリが引き受けられる。`*` を渡せる設計だが、validation では止めない
- GCP の Workload Identity Federation、Azure の Federated Credential も同じ OIDC 方式だが、条件の書き方（属性マッピング / subject の完全一致）が違う
- ロールチェーン（ロールからさらに AssumeRole）ではセッションが 1 時間に制限され、`max_session_duration` を伸ばしても効かない

## Test

`modules/iam-service-identity/tests/iam-service-identity.tftest.hcl`
