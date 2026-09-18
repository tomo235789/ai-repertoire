---
id: secret-fetch-at-runtime
lang: terraform
title: 秘密情報を実行時にシークレット管理サービスから取得する
tags: [シークレット, 秘密情報, 最小権限, 実行時取得, secret, secrets-manager, least-privilege, runtime]
lib: hashicorp/aws
fn: aws_secretsmanager_secret
since: "5.0"
verified: 2026-09-18
status: public
---

Secrets Manager のシークレット本体と、その値を読むだけの IAM ポリシーを作る。値は Terraform に書かず、アプリケーションが実行時に `GetSecretValue` で取得する。

## Signature

```hcl
variables: name, description?, kms_key_arn?, recovery_window_in_days? = 30, read_policy_name?, tags?
outputs:   secret_id, secret_arn, secret_name, read_policy_arn, read_policy_name
```

## Usage

```hcl
module "db_secret" {
  source      = "./modules/secret-fetch-at-runtime"
  name        = "example/app/db"
  description = "example app の DB 資格情報"
  tags        = { env = "example" }
}
# 実行ロールに読み取りを付ける: policy_arn = module.db_secret.read_policy_arn
```

## Contract

- 値を Terraform で設定しない。`aws_secretsmanager_secret_version` を作らないので state に平文が残らず、値の投入・更新はコンソール / CLI / ローテーションで行う
- 読み取りポリシーは `secretsmanager:GetSecretValue` のみを、このシークレットの ARN だけに許可する（ワイルドカードなし、Statement は 1 つ）
- `kms_key_arn` を渡すと、シークレットをその顧客管理キーで暗号化し、読み取りポリシーに `kms:Decrypt` を「そのキー ARN」かつ `kms:ViaService = secretsmanager.*.amazonaws.com` に限定して追加する。未指定なら AWS 管理キー `aws/secretsmanager` で暗号化し、KMS の権限は付けない
- `recovery_window_in_days` は 7〜30 のみ。0（復旧不可の即時削除）は validation で拒否する
- `kms_key_arn` は `arn:aws:kms:...:key/` 形式のみ。alias やキー ID は validation で拒否する
- `name` は Secrets Manager が許す文字（英数字と `/ _ + = . @ -`）のみ
- `read_policy_name` 未指定時は `name` の `/` を `-` に置換した `<name>-read`
- `tags` はシークレットと IAM ポリシーの両方に付く

## Alternatives

- SSM Parameter Store の `SecureString`（`aws_ssm_parameter`）: ローテーションやクロスアカウント共有が不要で、コストを抑えたいとき
- ECS / Lambda の `secrets` / 環境変数への Secrets Manager 参照: アプリ側で SDK を呼ばず、起動時にプラットフォームが注入する。値は起動時点で固定されるので、ローテーション後は再起動が必要
- 値も Terraform で管理したい場合は `aws_secretsmanager_secret_version` を別に置き、state を暗号化バックエンドに閉じ込めたうえで `ephemeral` / `write-only` 引数を使う

## Pitfalls

- 読み取りポリシーはロールに付けて初めて効く。`aws_iam_role_policy_attachment` は module の外
- シークレット名は削除後も復旧猶予中は再利用できない（`recovery_window_in_days` の間は同名で作れない）
- 顧客管理キーを使うときは、そのキーポリシーでも読み手の principal に `kms:Decrypt` を許可しておく（IAM ポリシーだけでは足りない）
- `GetSecretValue` は API 呼び出しごとに課金される。実行時に毎回呼ばず、プロセス内でキャッシュする（AWS の Secrets Manager caching ライブラリ）

## Test

`modules/secret-fetch-at-runtime/tests/secret-fetch-at-runtime.tftest.hcl`
