---
id: storage-object-versioning
lang: terraform
title: バケットのオブジェクトをバージョン管理して誤削除から守る
tags: [バージョニング, 誤削除防止, 世代管理, MFA Delete, S3, versioning, undelete]
lib: hashicorp/aws
fn: aws_s3_bucket_versioning
since: "5.0"
verified: 2026-09-18
status: public
---

「上書きや削除をしても前の状態に戻せるようにしたい」という要求に対する設定。バージョニングを有効にし、必要なら削除に MFA を必須にする。

## Signature

```hcl
module "x" { source = "./modules/storage-object-versioning", bucket_name, mfa_delete = false, mfa = null }
-> { bucket_name, versioning_status, mfa_delete_enabled, noncurrent_versions_retained_forever }
```

## Usage

```hcl
module "versioning" {
  source      = "./modules/storage-object-versioning"
  bucket_name = module.logs.bucket_id
}
# 古いバージョンが無限に溜まるので lifecycle と併用する
module "versions_retention" {
  source                             = "./modules/storage-bucket-lifecycle"
  bucket_name                        = module.versioning.bucket_name
  noncurrent_version_expiration_days = 30
}
```

## Contract

- `versioning_configuration.status` は常に `Enabled`。`versioning_status` 出力でも `Enabled` を返す
- `mfa_delete` の既定は `false`（`Disabled`）。`true` にすると `mfa`（デバイスのシリアル番号と現在のコード）が必須で、無ければ precondition で弾く。`mfa` は `sensitive`
- この module だけでは非現行バージョンが無期限に残る。`noncurrent_versions_retained_forever` 出力（常に `true`）と `bucket_name` 出力を `storage-bucket-lifecycle` の `bucket_name` / `noncurrent_version_expiration_days` に渡して保持期間を決める
- タグは付かない（`aws_s3_bucket_versioning` はタグを持たない）
- 冪等。既にバージョニング有効なバケットに apply しても差分は出ない

## Alternatives

- 「一定期間は誰にも消させない」要件（監査ログなど）は Object Lock（コンプライアンスモード）。バージョニングは削除を「削除マーカー」に変えるだけで、マーカーごと消せる
- 別リージョンへの複製（`aws_s3_bucket_replication_configuration`）はバージョニングが前提。災害対策はこの module の上に積む
- 個々のオブジェクトの変更履歴が業務データなら、バケットではなく DB 側で履歴テーブルを持つ方が検索しやすい

## Pitfalls

- バージョニングは一度有効にすると「無効」には戻せず「一時停止（Suspended）」になる。`terraform destroy` してもバケットの状態は Suspended のまま
- 削除は削除マーカーの追加で、ストレージも課金も減らない。`noncurrent_version_expiration_days` を付けないと容量が単調増加する
- MFA Delete はルートユーザーの MFA デバイスでしか有効化できず、CI からの apply では通らない。有効化は手動運用になることが多い
- GCS のオブジェクトバージョニング（`versioning.enabled`）は同じ意味論だが、Azure Blob の「バージョニング」と「ソフトデリート」は別機能で、誤削除対策は後者
- `bucket_name` はバケット ID（= 名前）。ARN を渡すと `NoSuchBucket` になる

## Test

`modules/storage-object-versioning/tests/storage-object-versioning.tftest.hcl`
