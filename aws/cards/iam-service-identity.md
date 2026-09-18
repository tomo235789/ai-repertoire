---
id: iam-service-identity
lang: aws
title: ワークロード用のサービス ID にリソースへのアクセスを与える
tags: [サービスID, 信頼ポリシー, OIDC, ワークロード, IAM, service principal, workload identity, trust policy]
lib: aws.iam
fn: service_identity_trust
since: "2024"
verified: 2026-09-18
status: public
---

「Lambda / ECS などの AWS サービス、または GitHub Actions / EKS などの OIDC で認証されたワークロードにロールを引き受けさせたい」という要求から、`create_role` に渡す信頼ポリシーを組み立てる。長期のアクセスキーを作らずに済ませるための入口。

## Signature

```python
def service_identity_trust(principal_kind: str, principal: str, conditions: Mapping[str, str | Sequence[str]] | None = None) -> dict[str, Any]
```

## Usage

```python
import json
import boto3
from iam_service_identity import service_identity_trust  # examples/iam-service-identity.py をコピー

trust = service_identity_trust("oidc", "arn:aws:iam::123456789012:oidc-provider/token.actions.githubusercontent.com",
                               {"sub": "repo:example-org/example-repo:ref:refs/heads/main", "aud": "sts.amazonaws.com"})
# trust["Statement"][0] == {"Effect": "Allow", "Principal": {"Federated": "arn:aws:iam::...:oidc-provider/..."},
#   "Action": "sts:AssumeRoleWithWebIdentity", "Condition": {"StringEquals": {"...:aud": "sts.amazonaws.com", "...:sub": "repo:..."}}}
boto3.client("iam").create_role(RoleName="example-deploy", AssumeRolePolicyDocument=json.dumps(trust))
service_identity_trust("service", "lambda.amazonaws.com", {"aws:SourceAccount": "123456789012"})  # AWS サービス向け
```

## Contract

- `principal_kind="service"`: `Principal.Service = principal`、`Action = sts:AssumeRole`。`conditions` は `aws:` で始まるキーのみ受け付け、ワイルドカード無しなら `StringEquals`、`aws:SourceArn` に `*` があれば `ArnLike`、その他の `*` は `StringLike`。`conditions` が空なら `Condition` キー自体が無い
- `principal_kind="oidc"`: `Principal.Federated = principal`（`:oidc-provider/` を含む ARN）、`Action = sts:AssumeRoleWithWebIdentity`。`<host>:sub` と `<host>:aud` の条件が**必須**（`host` は ARN の `oidc-provider/` 以降）。キーは `sub` / `aud` と書いても `<host>:` が補われる
- `aud` は常に `StringEquals`（ワイルドカードは `ValueError`）。`sub` は `*` / `?` を含むときだけ `StringLike`、それ以外は `StringEquals`
- 条件値がリストならソート・重複除去したリストになる。条件キーはソート順
- 文は常に `Allow` 1 つ。`Deny` は無い。同じ入力に同じ出力を返し、`json.dumps` できる
- `ValueError`: `principal_kind` が `service` / `oidc` 以外、`service` で `.amazonaws.com` で終わらない principal、`oidc` で `oidc-provider/` を含まないか host が空の ARN、`sub` / `aud` の欠落、空の条件値、`service` で `aws:` 以外の条件キー

## Alternatives

- Terraform module `terraform/modules/iam-service-identity`（同じ id。`aws_iam_openid_connect_provider` + `aws_iam_role`）
- CloudFormation `AWS::IAM::OIDCProvider` + `AWS::IAM::Role`
- EKS では IRSA（`<oidc>:sub = system:serviceaccount:<ns>:<sa>`）の代わりに EKS Pod Identity（`pods.eks.amazonaws.com` をサービスプリンシパルにし、`sts:TagSession` も許可する）が使える
- ECS タスクは `ecs-tasks.amazonaws.com`、Lambda は `lambda.amazonaws.com` を `service` で渡す。権限側は iam-least-privilege-role

## Pitfalls

- `AssumeRolePolicyDocument` は JSON 文字列。`json.dumps` してから渡す
- OIDC プロバイダ（`create_open_id_connect_provider`）はアカウントごとに URL 1 つ。GitHub の場合、`aud` は `sts.amazonaws.com`、`sub` は `repo:<org>/<repo>:ref:refs/heads/<branch>` や `repo:<org>/<repo>:environment:<env>`。`sub` を `repo:<org>/*` にすると組織内の全リポジトリから引き受けられる
- `sub` に `*` を書いて `StringEquals` にすると一致しない（この関数は自動で `StringLike` にする）。逆に `StringLike` は `repo:org/repo:*` が `repo:org/repo-fork:*` に一致しないが `repo:org/repo*` なら一致する。末尾は `:` で閉じる
- `aws:SourceAccount` / `aws:SourceArn` は「サービスが呼び出し元のリソースを伝える」場合にだけ評価される。Lambda の実行ロールには効かず（Lambda が付けない）、EventBridge / SNS / S3 通知などサービスがロールを引き受ける場面で効く
- 信頼ポリシーはロールを「誰が引き受けられるか」だけ決める。何ができるかは権限ポリシー側。両方揃えて初めて動く
- IAM の評価は「明示的 Deny > Allow」。組織の SCP で `sts:AssumeRoleWithWebIdentity` を制限していれば、この信頼ポリシーがあっても引き受けられない

## Test

`examples/iam-service-identity_test.py`
