---
id: secret-rotation
lang: terraform
title: 秘密情報を定期的に自動ローテーションする
tags: [シークレット, ローテーション, 自動更新, 秘密情報, secret, rotation, secrets-manager, lambda]
lib: hashicorp/aws
fn: aws_secretsmanager_secret_rotation
since: "5.0"
verified: 2026-09-18
status: public
---

既存の Secrets Manager シークレットに、Lambda による定期ローテーションを設定する。ローテーション Lambda 本体とその権限は module の外で用意する。

## Signature

```hcl
variables: secret_arn, rotation_lambda_arn, rotation_days? = 30, rotate_immediately? = true
outputs:   id, secret_arn, rotation_lambda_arn
```

## Usage

```hcl
module "db_secret_rotation" {
  source              = "./modules/secret-rotation"
  secret_arn          = module.db_secret.secret_arn
  rotation_lambda_arn = aws_lambda_function.rotate_db.arn
  rotation_days       = 30
  rotate_immediately  = false
}
```

## Contract

- `secret_arn` のシークレットを `rotation_lambda_arn` の Lambda で `rotation_days` 日ごとにローテーションする
- 既定は 30 日間隔、`rotate_immediately = true`（apply 直後に 1 回ローテーションして Lambda が動くことを確かめる）。両方とも変数で変えられる
- `rotation_days` は 1〜1000 の整数のみ。0 は validation で拒否する
- `secret_arn` / `rotation_lambda_arn` はそれぞれ `arn:aws:secretsmanager:...:secret:` / `arn:aws:lambda:...:function:` 形式のみ。名前だけの指定は validation で拒否する
- ローテーション Lambda の実行権限（Secrets Manager からの `lambda:InvokeFunction` 許可、Lambda が DB などへ接続するロール）は module の外。この module はローテーションのスケジュールだけを持つ
- `aws_secretsmanager_secret_rotation` はタグを持たないので `tags` 変数は無い
- 出力は入力をそのまま返す（`id` はシークレット ARN と同じ）

## Alternatives

- RDS / Redshift / DocumentDB の**マネージドローテーション**: `aws_rds_cluster` / `aws_db_instance` の `manage_master_user_password = true` を使えば Lambda 不要で AWS がローテーションする
- 日数ではなく cron / rate で指定したいときは `rotation_rules.schedule_expression`（`automatically_after_days` と排他）
- ローテーションが不要な静的な API キーなどは、この module を付けずに有効期限の運用で管理する

## Pitfalls

- Lambda 側の `aws_lambda_permission`（principal `secretsmanager.amazonaws.com`）が無いとローテーションは失敗する。`rotate_immediately = true` なら apply 時点で失敗が分かる
- ローテーション中は `AWSPENDING` / `AWSCURRENT` の 2 版が存在する。読み手が `AWSCURRENT` を取り直さないと古い値を使い続ける
- ローテーションを外す（resource を destroy する）とスケジュールは消えるが、シークレットの値は残る
- Lambda は VPC 内の DB に届くサブネットとセキュリティグループに置く。Secrets Manager の VPC エンドポイントも必要になる

## Test

`modules/secret-rotation/tests/secret-rotation.tftest.hcl`
