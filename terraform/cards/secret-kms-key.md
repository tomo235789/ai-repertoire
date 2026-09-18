---
id: secret-kms-key
lang: terraform
title: 顧客管理の暗号鍵を作って保存データを暗号化する
tags: [暗号鍵, KMS, 顧客管理キー, 保存時暗号化, キーポリシー, kms, cmk, encryption-at-rest]
lib: hashicorp/aws
fn: aws_kms_key
since: "5.0"
verified: 2026-09-18
status: public
---

自動ローテーション付きの対称 KMS キーと別名を作る。キーポリシーは「ルート」「管理者」「利用者」を分けて最小化する。

## Signature

```hcl
variables: alias_name, account_id, description?, partition? = "aws", allow_root_full_access? = true,
           admin_principal_arns? = [], user_principal_arns? = [], deletion_window_in_days? = 30, tags?
outputs:   key_id, key_arn, alias_name, alias_arn
```

## Usage

```hcl
module "app_key" {
  source               = "./modules/secret-kms-key"
  alias_name           = "alias/example/app"
  account_id           = "123456789012"
  description          = "example app の保存データ暗号化"
  admin_principal_arns = ["arn:aws:iam::123456789012:role/example-key-admin"]
  user_principal_arns  = ["arn:aws:iam::123456789012:role/example-app"]
  tags                 = { env = "example" }
}
```

## Contract

- `enable_key_rotation = true` を固定で有効にする（年次の自動ローテーション。変数で無効にできない）
- 対称キー（`key_usage = ENCRYPT_DECRYPT`）
- 別名は必須。`alias/` で始まらない名前と、AWS 管理キー用の `alias/aws/` は validation で拒否する
- キーポリシーは 3 種の Statement を variable で分ける
  - `allow_root_full_access = true`（既定）: `arn:<partition>:iam::<account_id>:root` に `kms:*`。IAM ポリシーでもキーを管理でき、締め出し事故を防ぐ
  - `admin_principal_arns`: 管理操作（`Create* / Describe* / Enable* / List* / Put* / Update* / Revoke* / Disable* / Get* / Delete* / TagResource / UntagResource / ScheduleKeyDeletion / CancelKeyDeletion`）のみ。`kms:Encrypt` / `kms:Decrypt` は含まない
  - `user_principal_arns`: 暗号化・復号（`Encrypt / Decrypt / ReEncrypt* / GenerateDataKey* / DescribeKey`）のみ。`PutKeyPolicy` / `ScheduleKeyDeletion` は含まない
  - 空のリストの Statement は出力しない（既定はルートの 1 Statement だけ）
- `allow_root_full_access = false` かつ `admin_principal_arns` が空（誰もポリシーを直せないキー）は precondition で拒否する
- `deletion_window_in_days` は 7〜30 のみ。既定 30 日（削除予約を取り消せる猶予）
- `account_id` は 12 桁の数字のみ
- `tags` はキーに付く（`aws_kms_alias` はタグを持たない）

## Alternatives

- AWS 管理キー（`aws/s3`、`aws/secretsmanager` など）: キーポリシーやクロスアカウント共有が不要なら無料で、多くのサービスの既定
- 非対称キーや HMAC キーは `key_usage` / `customer_master_key_spec` が違うので別 module にする
- マルチリージョン複製が必要なら `multi_region = true` と `aws_kms_replica_key` を別途追加する

## Pitfalls

- キーポリシーの `Principal` に存在しない ARN を書くと apply が `MalformedPolicyDocumentException` で失敗する。ロールを先に作る
- `allow_root_full_access = false` にすると、IAM ポリシーだけではキーを使えなくなる。管理者ロールの資格情報を失うとキーは復旧できない
- キー削除は最短 7 日待つ。削除されたキーで暗号化したデータは二度と復号できない
- 別名（`alias/...`）は削除しても即再利用できるが、キー ID を参照している他リソースは張り替えが必要。他リソースからは `key_arn` ではなく別名で参照すると付け替えが楽

## Test

`modules/secret-kms-key/tests/secret-kms-key.tftest.hcl`
