---
id: database-backup-retention
lang: terraform
title: データベースの自動バックアップと保持期間を設定する
tags: [自動バックアップ, PITR, バックアップ保持期間, スナップショット, マテンナンスウィンドウ, 最終スナップショット, コスト配賦, リカバリ]
lib: hashicorp/aws
fn: aws_db_instance
since: "5.0"
verified: 2026-09-18
status: public
---

「バックアップの範囲と期間を明示したい」という要求に対する設定。自動バックアップの有効化・保持日数・バックアップ時間帯・コピー先スナップショットのタグ付けを variable で受ける。暗号化や非公開アクセスなど基本構成は内側でデフォルトにしている。

## Signature

```hcl
module "x" { source = "./modules/database-backup-retention", identifier, engine, engine_version, db_subnet_group_name, vpc_security_group_ids, backup_retention_period = 7, backup_window, copy_tags_to_snapshot = true, delete_automated_backups = false, final_snapshot_identifier, tags = {} }
-> { id, arn, backup_retention_period }
```

## Usage

```hcl
module "db" {
  source                    = "./modules/database-backup-retention"
  identifier                = "app-db"
  engine                    = "postgres"
  db_subnet_group_name      = "private-us-east-2a"
  vpc_security_group_ids    = [module.app_sg.security_group_id]
  backup_retention_period   = 30           # 1〜35 日
  backup_window             = "03:00-04:00"
  final_snapshot_identifier = "app-db-final-v2"
}
```

## Contract

- 自動バックアップの保持日数は `backup_retention_period` で決まる（既定: 7 日）。値域は 1〜35 日で、0 は自動バックアップとポイントインタイムリカバリを無効にするため validation で弾く
- バックアップ時間帯は `backup_window`（UTC の hh24:mi-hh24:mi）で指定。30 分以上という AWS の制約に合わせて validation がフォーマットをチェックする
- コピータグ: `copy_tags_to_snapshot = true` が既定。コスト配賦や保持ポリシーの根拠としてスナップショットにもインスタンスのタグが引き継がれる
- 削除時の自動バックアップ: 既定 `false`（保持期間切れるまで残る）。`true` にすると同時に削除される
- スキップなし最終スナップショット: `skip_final_snapshot = false` で固定。`final_snapshot_identifier` で名前を指定できる（英字始まり・ハイフン可・末尾ハイフン不可）
- 最小構成は内側で暗号化済み（`storage_encrypted = true`）、非公開（`publicly_accessible = false`）、マスターパスワード自動生成（`manage_master_user_password = true`）
- `engine` の既定は postgres。validation で postgres / mysql / mariadb のみに限定する
- `tags` は DB インスタンスに付く

## Alternatives

- `aws/examples/database-backup-retention.py`（Boto3 で同じ設定を関数として書く例）
- AWS Backup でのクロスリージョンバックアップ — 同じリソースに対し Terraform と AWS Backup の両方が管理すると競合するので、どちらかを一元化する
- RDS スナップショットの手動コピー — Terraform から `aws_db_snapshot` を使えばよいが、この module は削除時の振る舞いに特化している

## Pitfalls

- `backup_retention_period` を 0 にすると自動バックアップ自体が無効になり、PITR（ポイントインタイムリカバリ）もできなくなる。validation で阻止するが呼び出し側の意図確認は必要
- バックアップ時間帯は UTC なので JST の深夜帯に設定する場合は -9 時間する（例: JST 03:00 = UTC 18:00前一晚）
- インスタンス削除時の自動バックアップを消す (`delete_automated_backups = true`) と、PITR の対象外になる。スナップショットを残すのと同時には効かない

## Test

`modules/database-backup-retention/tests/database-backup-retention.tftest.hcl`
