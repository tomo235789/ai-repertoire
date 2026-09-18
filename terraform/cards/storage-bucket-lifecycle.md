---
id: storage-bucket-lifecycle
lang: terraform
title: バケットのオブジェクトを保持期間で自動的に移行・削除する
tags: [ライフサイクル, 保持期間, 自動削除, ストレージクラス移行, S3, lifecycle, retention, expiration]
lib: hashicorp/aws
fn: aws_s3_bucket_lifecycle_configuration
since: "5.0"
verified: 2026-09-18
status: public
---

「ログは 30 日で安いクラスへ、1 年で消したい」という要求に対する設定。移行・削除・非現行バージョン削除・未完了マルチパート中止を 1 つの規則にまとめる。

## Signature

```hcl
module "x" { source = "./modules/storage-bucket-lifecycle", bucket_name, prefix = "", transition_days = null, transition_storage_class = "STANDARD_IA",
             expiration_days = null, noncurrent_version_expiration_days = null, abort_incomplete_multipart_days = 7 }
-> { bucket_name, rule_id, rule_status }
```

## Usage

```hcl
module "logs_retention" {
  source                             = "./modules/storage-bucket-lifecycle"
  bucket_name                        = module.logs.bucket_id
  prefix                             = "logs/"
  transition_days                    = 30  # 30 日で STANDARD_IA へ
  expiration_days                    = 365 # 1 年で削除
  noncurrent_version_expiration_days = 30  # 古いバージョンは 30 日で削除
}
```

## Contract

- 規則は 1 つ、`status = "Enabled"`、`filter.prefix` は `prefix`（既定 `""` = バケット全体）
- `transition_days` 日後に `transition_storage_class`（既定 `STANDARD_IA`）へ移行し、`expiration_days` 日後に現行バージョンを削除する。`null` の項目はブロック自体を生成しない
- 非現行バージョンは `noncurrent_version_expiration_days` 日後に削除する（バージョニング有効時のみ意味を持つ）
- 未完了のマルチパートアップロードは既定で 7 日後に中止する（見えない課金の取りこぼしを防ぐ）
- 弾く入力: 移行より前の削除（`expiration_days <= transition_days`）、`STANDARD_IA` / `ONEZONE_IA` への 30 日未満の移行、負数・小数の日数、未対応のストレージクラス、4 項目すべて `null`
- タグは付かない（`aws_s3_bucket_lifecycle_configuration` はタグを持たない）
- 冪等。`rule_id` を変えると規則は置き換わるがオブジェクトには影響しない

## Alternatives

- アクセスパターンが読めないなら `transition_storage_class = "INTELLIGENT_TIERING"` にして S3 に任せる（30 日制約が無く、監視料金がかかる）
- 「削除させない」保護が目的なら Object Lock（`aws_s3_bucket_object_lock_configuration`）。ライフサイクルは削除を促す側の仕組み
- バージョニングの有効化そのものは `storage-object-versioning`。このカードは非現行バージョンの寿命だけを扱う

## Pitfalls

- 規則は非同期に実行される。期限が来ても削除は「その日のうちのどこか」で、即時ではない
- `STANDARD_IA` / `ONEZONE_IA` は最低保存 30 日・最小課金 128 KB。小さなオブジェクトを移すと逆に高くなる
- `prefix` は先頭一致（`logs/` は `logs/2026/...` に効き、`archive/logs/` には効かない）。tag で絞りたいときは `filter` を拡張する
- GCS のライフサイクルは「経過日数」を同じく `age` で持つが、Azure Blob は「最終更新 / 最終アクセスからの日数」で、意味が違う
- 1 つのバケットに `aws_s3_bucket_lifecycle_configuration` は 1 つだけ。別 module で 2 つ目を付けると互いに上書きし合う

## Test

`modules/storage-bucket-lifecycle/tests/storage-bucket-lifecycle.tftest.hcl`
