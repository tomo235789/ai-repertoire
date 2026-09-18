---
id: iam-read-only-policy
lang: aws
title: 読み取り専用のアクセスポリシーを作る
tags: [読み取り専用, 参照権限, ポリシー, IAM, read-only, policy, viewer, audit]
lib: aws.iam
fn: read_only_policy
since: "2024"
verified: 2026-09-18
status: public
---

「閲覧・監査・監視だけできればよい」という要求から、`Get*` / `List*` / `Describe*` に限ったポリシー文書を組み立てる。書き込み系の action や、名前は `Get*` でも秘密値を返す action は入力の時点で拒否する。

## Signature

```python
def read_only_policy(actions: Iterable[str], resources: Iterable[str]) -> dict[str, Any]
```

## Usage

```python
import json
import boto3
from iam_read_only_policy import read_only_policy  # examples/iam-read-only-policy.py をコピー

policy = read_only_policy(["s3:GetObject", "s3:ListBucket"], ["arn:aws:s3:::example-bucket", "arn:aws:s3:::example-bucket/*"])
# policy["Statement"] == [{"Sid": "ReadOnly", "Effect": "Allow", "Action": ["s3:GetObject", "s3:ListBucket"], "Resource": [...]}]
boto3.client("iam").create_policy(PolicyName="example-read-only", PolicyDocument=json.dumps(policy))

read_only_policy(["ec2:DescribeInstances", "s3:Get*"], ["*"])  # Describe 系は "*" が必要。末尾の * は許す
```

## Contract

- `Allow` 文 1 つ（`Sid: ReadOnly`）だけ。`Deny` 文は無い
- `Action` は `<service>:Get...` / `<service>:List...` / `<service>:Describe...` のみ（大文字小文字を区別。`s3:get*` は不可）。末尾の `*`（`s3:Get*`）だけ許し、`*` 単体・`s3:*`・`*:GetObject` は `ValueError`
- 秘密値や一時資格情報を返す `secretsmanager:GetSecretValue` / `ssm:GetParameter` / `ssm:GetParameters` / `ssm:GetParametersByPath` / `sts:GetFederationToken` / `sts:GetSessionToken` は `Get*` でも `ValueError`
- `Resource` は `arn:` で始まる文字列か `*`。`*` を許すのは `Describe*` / `List*` 系がリソースレベル制御に対応しないため
- `Action` / `Resource` は重複除去・ソート済み。同じ入力に同じ出力を返し、`json.dumps` できる
- `ValueError`: `actions` / `resources` が空、上記の形式に合わない action、ARN でも `*` でもない resource

## Alternatives

- Terraform module `terraform/modules/iam-read-only-policy`（同じ id。`aws_iam_policy_document` + `aws_iam_policy`）
- CloudFormation `AWS::IAM::ManagedPolicy` の `PolicyDocument`
- サービスを限定しない監査用途なら AWS 管理ポリシー `ReadOnlyAccess`（ただし S3 オブジェクトの中身や DynamoDB の項目も読める）や `ViewOnlyAccess`（メタデータのみ）。管理ポリシーは更新される点に注意
- 読み取りを「特定のロールにだけ」与えるなら iam-least-privilege-role にこのポリシーの action を渡す

## Pitfalls

- `PolicyDocument` は JSON 文字列。`json.dumps` してから渡す
- `Get*` は「メタデータの参照」ではなく「データの取得」も含む。`s3:GetObject` / `dynamodb:GetItem` / `kinesis:GetRecords` は個人情報を読める。監査だけなら `List*` / `Describe*` に絞る
- 拒否リストは代表的な 6 つだけ。`lambda:GetFunction`（コードのダウンロード URL を返す）や `ecr:GetAuthorizationToken` など、用途によっては危険な `Get*` が他にもある。`Action` を必ず目視する
- IAM は明示的 Deny が勝つ。SCP で拒否されていれば `Allow` しても読めない。逆に他のポリシーで書き込みを許可していればこのポリシーは書き込みを止めない（`Deny` 文を出さないため）
- `Describe*` 系は `Resource` に ARN を指定しても効かない（`*` が必要）。ARN を渡してもエラーにならず、単に権限が無い状態になる
- 管理ポリシーは 6144 文字まで。action が多い場合は複数のポリシーに分ける

## Test

`examples/iam-read-only-policy_test.py`
