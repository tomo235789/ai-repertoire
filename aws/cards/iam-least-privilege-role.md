---
id: iam-least-privilege-role
lang: aws
title: 特定の操作だけを許可する最小権限のロールを作る
tags: [最小権限, ロール, 信頼ポリシー, IAM, least privilege, role, policy, permissions boundary]
lib: aws.iam
fn: least_privilege_role
since: "2024"
verified: 2026-09-18
status: public
---

「この AWS サービスから、この操作だけを、このリソースにだけ許す」という要求から、boto3 の `create_role` / `put_role_policy` に渡す信頼ポリシーと権限ポリシーを組み立てる。ワイルドカードは入力の時点で拒否する。

## Signature

```python
def least_privilege_role(name: str, trusted_service: str, actions: Iterable[str], resources: Iterable[str], permissions_boundary: str | None = None, source_account: str | None = None) -> dict[str, Any]
```

## Usage

```python
import json
import boto3
from iam_least_privilege_role import least_privilege_role  # examples/iam-least-privilege-role.py をコピー

cfg = least_privilege_role("example-role", "lambda.amazonaws.com", actions=["s3:GetObject"], resources=["arn:aws:s3:::example-bucket/*"])
iam = boto3.client("iam")
iam.create_role(RoleName=cfg["role_name"], AssumeRolePolicyDocument=json.dumps(cfg["assume_role_policy"]))
iam.put_role_policy(RoleName=cfg["role_name"], PolicyName=cfg["policy_name"], PolicyDocument=json.dumps(cfg["policy"]))
# cfg["policy"]["Statement"] == [{"Sid": "LeastPrivilege", "Effect": "Allow", "Action": ["s3:GetObject"], "Resource": ["arn:aws:s3:::example-bucket/*"]}]
```

## Contract

- `assume_role_policy` は `Allow` 文 1 つ: `Principal.Service = trusted_service`、`Action = sts:AssumeRole`。`source_account` を渡すと `Condition.StringEquals["aws:SourceAccount"]` が付く（混乱した代理の防止）
- `policy` は `Allow` 文 1 つ（`Sid: LeastPrivilege`）で、`Action` と `Resource` は渡した値をそのまま（重複除去・ソート済み）。`Deny` 文や暗黙の追加権限は無い
- `Action` は `<service>:<Action>` 形式のみ。`*`、`s3:*`、`s3:Get*` のような部分ワイルドカードも `ValueError`
- `Resource` は `arn:` で始まる文字列のみ。`*` 単体は `ValueError`（`arn:aws:s3:::example-bucket/*` のような ARN 内の `*` は許す）
- `policy_name` は `<name>-policy`。`permissions_boundary` は渡したときだけキーが存在し、値は ARN そのまま
- 同じ入力に同じ出力を返し、入力のリストを変更しない。`json.dumps` できる
- `ValueError`: `actions` / `resources` が空、ロール名が `[A-Za-z0-9_+=,.@-]{1,64}` に合わない、`trusted_service` が `.amazonaws.com` で終わらない、`permissions_boundary` に `:policy/` が無い、`source_account` が 12 桁でない

## Alternatives

- Terraform module `terraform/modules/iam-least-privilege-role`（同じ id。`aws_iam_role` + `aws_iam_role_policy`）
- CloudFormation `AWS::IAM::Role` の `AssumeRolePolicyDocument` と `Policies`
- 複数ロールで同じ権限を共有するならインラインではなく `create_policy` + `attach_role_policy`（`policy` をそのまま `PolicyDocument` に渡せる）
- 人間の一時的な操作には IAM Identity Center の Permission Set。ロールを直接作らない

## Pitfalls

- `AssumeRolePolicyDocument` / `PolicyDocument` は JSON 文字列。dict のまま渡すと `ParamValidationError`
- IAM は「明示的 Deny > Allow > 暗黙の Deny」。この関数は Allow しか出さないので、SCP や Permissions Boundary で Deny されていれば操作は失敗する。境界を渡した場合、実効権限は `policy` と境界の**積集合**
- `create_role` の直後は伝播に数秒かかり、すぐ `sts:AssumeRole` や Lambda 作成に使うと `InvalidParameterValueException` になることがある。リトライする
- 同名ロールがあると `EntityAlreadyExists`。信頼ポリシーの更新は `update_assume_role_policy`、権限の更新は `put_role_policy` の再実行（上書き）で行う
- `ec2:Describe*` などリソースレベル制御に対応しない action は ARN を指定しても効かず `*` が必要になる。それらは iam-read-only-policy で別ポリシーにする
- `iam:PassRole` を許すと別ロールの権限を渡せてしまう。含めるなら `Resource` を渡す先のロール ARN に限定する

## Test

`examples/iam-least-privilege-role_test.py`
