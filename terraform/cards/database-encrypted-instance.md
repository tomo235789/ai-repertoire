---
id: database-encrypted-instance
lang: terraform
title: 保存時暗号化を有効にしたデータベースインスタンスを作る
tags: [保存時暗号化, KMS, マスターパスワード自動生成, Performance Insights, ストレージ暗号化, AWS Managed Key, データベース, 機密情報保護]
lib: hashicorp/aws
fn: aws_db_instance
since: "5.0"
verified: 2026-09-18
status: public
---

「インスタンスが自動的に暗号化され、パスワードも Secrets Manager が保管する」PostgreSQL インスタンス。暗号化の 3 か所（ストレージ / マスターパスワード / Performance Insights）を同じ KMS キーで統一し、Terraform の state に平文のパスワードを書かない。

## Signature

```hcl
module "x" { source = "./modules/database-encrypted-instance", identifier, engine_version, db_name, db_subnet_group_name, vpc_security_group_ids, kms_key_id = null, instance_class = "db.t4g.medium", allocated_storage = 20, deletion_protection = true, multi_az = false, performance_insights_retention_period = 7, tags = {} }
-> { id, arn, address, port, master_user_secret_arn }
```

## Usage

```hcl
module "app_db" {
  source                   = "./modules/database-encrypted-instance"
  identifier               = "app-db"
  engine_version           = "16"
  db_name                  = "app"
  db_subnet_group_name     = "private-us-east-2a"
  vpc_security_group_ids   = [module.app_sg.security_group_id]
  kms_key_id               = module.db_kms.key_arn    # null なら AWS 管理キー
}
# module.app_db.master_user_secret_arn を IAM ポリシーの Resource に渡す
```

## Contract

- 保存時暗号化: `kms_key_id` が `null` なら AWS 管理キー（`aws/rds`）、渡せば指定の KMS キー。ストレージ・マスターパスワード・Performance Insights の 3 か所に同じ鍵が適用される
- パスワード管理: `manage_master_user_password = true`。`master_user_secret_arn` 出力で Secrets Manager の ARN を確認できる。Terraform の state に平文のパスワードは書かない
- 公開アクセス禁止: `publicly_accessible = false` で固定。外部 IP から直接接続できない
- Performance Insights: 既定で有効、保持期間 7 日（無料枠）。有料期間（31 の倍数）に設定できるのは contract と validation で強制する
- マイナーバージョン自動更新: `auto_minor_version_upgrade = true` で固定
- 削除保護: 既定 `true`。本番は true のまま、破棄する直前だけ false にする
- 最終スナップショット: `skip_final_snapshot = false`（常に取る）。スナップショット名は `<identifier>-final`、タグを引き継ぐ
- `tags` は DB インスタンスに付く。サブネットグループやセキュリティグループには付かない
- `kms_key_id` に KMS の ARN 以外（エイリアス / キー ID だけ）を渡すと validation で弾く
- `identifier` / `allocated_storage` / `performance_insights_retention_period` も validation で不正値を弾く

## Alternatives

- `aws/examples/database-encrypted-instance.py`（Boto3 で同じ設定を関数として書く例）
- AWS RDS コンソールの「暗号化」チェックボックス — 同じ KMS キーの選択 UI があるが、再現性がない
- クロスリージョンレプリカで暗号化済みデータを移すときは `database-read-replica` を使う（暗号化は自動伝播）

## Pitfalls

- `kms_key_id` を変えるとインスタンスの再作成になる。既存インスタンスに KMS キーを後から付けることは RDS API でできない
- パスワードを復元するには Secrets Manager の ARN を使う。state にパスワードが残っていないので、失効したら再度 `manage_master_user_password = true` に切り替える
- Performance Insights の保持期間を変更すると再作成になる場合がある。7 日（無料）と 31 日倍数（有料）以外は弾く
- DB インスタンス名はリージョン内で一意。同じ VPC / サブネットの中で別のモジュールが同じ `identifier` を使わないよう命名規則を決めておく

## Test

`modules/database-encrypted-instance/tests/database-encrypted-instance.tftest.hcl`
