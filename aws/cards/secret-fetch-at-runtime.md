---
id: secret-fetch-at-runtime
lang: aws
title: 秘密情報を実行時にシークレット管理サービスから取得する
tags: [シークレット, リソースポリシー, 最小権限, Secrets Manager, secret, resource-policy, read-only, kms]
lib: aws.secretsmanager
fn: secret_and_read_policy
since: "2024"
verified: 2026-09-18
status: public
---

「実行時にシークレットを取得し、特定の IAM プリンシパルだけが読めるようにする」という要求から、`create_secret` の kwargs と `put_resource_policy` に渡すリソースポリシーを組み立てる。SecretString / SecretBinary 自体は関数で扱わず、GetSecretValue で取得する前提。

## Signature

```python
def secret_and_read_policy(name: str, kms_key_id: str | None = None, reader_principal_arns: Sequence[str] = (), *, description: str | None = None, tags: Mapping[str, str] | None = None) -> dict[str, Any]
```

## Usage

```python
from secret_fetch_at_runtime import secret_and_read_policy  # examples/secret-fetch-at-runtime.py をコピー

out = secret_and_read_policy("app/prod/db", kms_key_id="alias/db-key", reader_principal_arns=[ROLE])
sm.create_secret(**out["create_secret"])                      # Name / Description / KmsKeyId / Tags
sm.put_resource_policy(SecretId="app/prod/db", ResourcePolicy=out["read_policy"])  # Allow + Deny の 2 文
```

## Contract

- `read_policy` は `Allow` 文（GetSecretValue を reader_principal_arns に許可）と `Deny` 文（一覧外のプリンシパルを ArnNotEquals で拒否）の 2 つからなる
- `Deny` 文の `Principal.AWS` は `"*"`。条件で `aws:PrincipalArn` が reader_principal_arns に含まれないものを弾く
- `create_secret` に `SecretString` / `SecretBinary` は含まれない。引数として受け取らない（TypeError）
- `kms_key_id` を渡さなければ `KmsKeyId` を含めず、AWS 管理キー `aws/secretsmanager` が既定で使われる
- `tags` を渡すとキー順にソートしたリストを返す。空か `None` のときは含めない
- 同じ入力に同じ出力を返し、入力の `reader_principal_arns` / `tags` を変更しない。全体を `json.dumps` できる
- `ValueError`: シークレット名が `/_=+.@-` で 1〜512 文字未満、reader_principal_arns が空 / 重複 / ワイルドカード / IAM 形式外 / SQS など他サービスの ARN

## Alternatives

- Terraform module `terraform/modules/secret-fetch-at-runtime`（同じ id。`aws_secretsmanager_secret` + `aws_secretsmanager_secret_policy` を同じ既定値で）
- CloudFormation `AWS::SecretsManager::Secret` + `AWS::SecretsManager::ResourcePolicy`。リソースポリシーは IAM ポリシーではなくシークレットに直接付けるもの

## Pitfalls

- リソースポリシーの `Deny` は Allow より優先されるが、同一プリンシパルに対して Deny がなければ Effect がない。ArnNotEquals で一覧外を弾くのが核心
- `put_resource_policy` に渡すのは dict。AWS CLI では `--resource-policy` が JSON 文字列なので注意
- `reader_principal_arns` に `*` や IAM 形式外の ARN を渡すと ValueError になる。SQS / SNS の ARN と混同しない
- KMS 鍵を指定すると、シークレットの暗号化と復号にその CMK が必要になる。読み手ロールに `kms:Decrypt` も追加する

## Test

`examples/secret-fetch-at-runtime_test.py`
