---
id: iam-read-only-policy
lang: terraform
title: 読み取り専用のアクセスポリシーを作る
tags: [読み取り専用, IAM ポリシー, 管理ポリシー, 閲覧権限, read-only, iam-policy, managed-policy]
lib: hashicorp/aws
fn: aws_iam_policy
since: "5.0"
verified: 2026-09-18
status: public
---

「監査担当や監視ツールに、読むだけの権限を渡したい」という要求に対する設定。`Get*` / `List*` / `Describe*` 以外のアクションを validation で弾く顧客管理ポリシーを作る。

## Signature

```hcl
module "x" { source = "./modules/iam-read-only-policy", name, allowed_actions, resource_arns, description = "Read-only access", path = "/", tags = {} }
-> { policy_arn, policy_name, policy_json }
```

## Usage

```hcl
module "logs_read_only" {
  source          = "./modules/iam-read-only-policy"
  name            = "example-logs-read-only"
  allowed_actions = ["s3:GetObject", "s3:ListBucket", "s3:GetBucketLocation"]
  resource_arns   = [module.logs.bucket_arn, "${module.logs.bucket_arn}/*"]
  tags            = { env = "prod" }
}
# module.logs_read_only.policy_arn を aws_iam_role_policy_attachment に渡す
```

## Contract

- ポリシーは `Allow` 1 文で、`Action` は `allowed_actions`、`Resource` は `resource_arns` とそのまま一致する。`Deny` 文は含まない
- `allowed_actions` は `<service>:Get…` / `List…` / `Describe…`（末尾 `*` 可。例 `ec2:Describe*`）だけを受け付ける。`s3:PutObject`、`s3:DeleteObject`、`kms:Decrypt`、`s3:*`、`*` は validation で弾く
- `resource_arns` は `arn:` で始まる ARN か `"*"`。`Describe*` / `List*` のようにリソースレベル権限が無いアクションのために `["*"]` を受け付ける。ARN でも `*` でもない値は弾く
- `path` の既定は `/`、`description` の既定は `Read-only access`。`tags` はポリシーに付く
- `policy_json` 出力はポリシー本文の JSON。スナップショット比較に使える
- 冪等。ポリシー本文の変更は新バージョンとして反映され、attach 先には影響しない

## Alternatives

- AWS 管理の `ReadOnlyAccess`（`arn:aws:iam::aws:policy/ReadOnlyAccess`）は全サービスの読み取りで、S3 のオブジェクト本文も読める。対象を絞りたいときだけこのカード
- 「読み取り + 特定の書き込み」が要るなら `iam-least-privilege-role` に action を列挙する。このカードは書き込みを構造的に排除するのが目的
- 監査用の閲覧だけなら `SecurityAudit` / `ViewOnlyAccess`（メタデータのみ、データ本文は読めない）の方が安全なことが多い

## Pitfalls

- `Get*` / `List*` / `Describe*` でも `s3:GetObject` はデータ本文の読み取り、`secretsmanager:GetSecretValue` は秘密情報の取得。「読み取り = 無害」ではない。`resource_arns` で対象を絞る
- `dynamodb:Query` / `Scan`、`sqs:ReceiveMessage`、`kms:Decrypt` は読み取り相当だが接頭辞が違うので弾かれる。必要なら `iam-least-privilege-role` で明示する
- `ec2:Describe*` / `cloudwatch:List*` はリソースレベル権限が無く、`Resource: "*"` でしか書けない。ARN を渡すと有効な ARN でも `AccessDenied` になる
- ポリシー名はアカウント内で一意（128 文字まで）。`name` / `path` / `description` の変更は再作成で、attach 先から一度外れる
- GCP の「viewer」ロール、Azure の「Reader」は事前定義でサービス横断。AWS で同じ粒度を求めるなら `ViewOnlyAccess` が近い

## Test

`modules/iam-read-only-policy/tests/iam-read-only-policy.tftest.hcl`
