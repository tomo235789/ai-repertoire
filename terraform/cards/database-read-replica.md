---
id: database-read-replica
lang: terraform
title: 読み取り負荷を分散するリードレプリカを作る
tags: [リードレプリカ, クロスリージョン, データベース複製, マスターパスワード自動生成, 非公開アクセス, リード専用, 高可用性]
lib: hashicorp/aws
fn: aws_db_instance
since: "5.0"
verified: 2026-09-18
status: public
---

「プライマリと同じデータをリードオンリーで持たせたい」という要求に対する設定。同一リージョンでは KMS サブネットグループを省略して元から引き継ぎ、クロスリージョンでは複製先リージョンの資源を明示する。暗号化・非公開アクセスは常に有効。

## Signature

```hcl
module "x" { source = "./modules/database-read-replica", identifier, replicate_source_db, vpc_security_group_ids, instance_class = "db.t4g.medium", kms_key_id = null, db_subnet_group_name = null, backup_retention_period = 0, multi_az = false, tags = {} }
-> { id, arn, address }
```

## Usage

```hcl
module "ro" {  # 同一リージョン。鍵とサブネットグループはプライマリを引き継ぐ
  source                 = "./modules/database-read-replica"
  identifier             = "app-db-ro"
  replicate_source_db    = module.primary.id  # クロスリージョンなら ARN + kms_key_id が必須
  vpc_security_group_ids = [module.app_sg.security_group_id]
}
```

## Contract

- 同一リージョン: `kms_key_id` と `db_subnet_group_name` は省略可能。元インスタンスから自動伝播する
- クロスリージョン: `replicate_source_db` が ARN の場合、`kms_key_id` と `db_subnet_group_name` が必須（validation で強制）
- 保存時暗号化: 元が暗号化済みならレプリカも暗号化される。クロスリージョンでは複製先リージョンの KMS キーを使う
- 公開アクセス禁止: `publicly_accessible = false` で固定
- バックアップ: レプリカ自身の保持期間の既定は 0（元インスタンスでバックアップを取る前提）
- スナップショット: レプリカは削除時に最終スナップショットを取れない（`skip_final_snapshot = true`）
- `tags` はレプリカインスタンスに付く。複製元のタグはコピーされない
- `identifier` / `backup_retention_period` も validation で不正値を弾く

## Alternatives

- `aws/examples/database-read-replica.py`（Boto3 で同じ設定を関数として書く例）
- AWS RDS スナップショットからの復元 — スナップショットをコピーしてインスタンスを立てる。レプリカより遅いがフルコピーが要るときに使う
- Aurora Multi-Master — RDS 外のリードレプリカパターン。この module は標準の RDS レプリカ向け

## Pitfalls

- クロスリージョンレプリカは KMS キーを明示しないと同リージョンと勘違いしてデフォルトキーで暗号化されるかもしれない。validation で阻止するが意図の確認が要る
- レプリカ自体はリードオンリーなので、直接 `INSERT` / `UPDATE` できない（アプリケーション側が書き先のインスタンスを切り替える必要がある）
- レプリカへのバックアップ保持期間を大きくすると、レプリカ側のストレージコストが余分に掛かる。元のインスタンスと重複することになる

## Test

`modules/database-read-replica/tests/database-read-replica.tftest.hcl`
