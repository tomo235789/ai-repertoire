---
id: storage-bucket-private
lang: terraform
title: 公開アクセスを禁止したオブジェクトストレージのバケットを作る
tags: [非公開バケット, 公開アクセス禁止, 保存時暗号化, S3, private-bucket, block-public-access, encryption]
lib: hashicorp/aws
fn: aws_s3_bucket
since: "5.0"
verified: 2026-09-18
status: public
---

「インターネットに一切公開しないバケットが欲しい」という要求に対する設定。公開アクセスブロック・ACL 無効化・保存時暗号化・TLS 必須のバケットポリシーを 1 つの module にまとめる。

## Signature

```hcl
module "x" { source = "./modules/storage-bucket-private", name, kms_key_arn = null, force_destroy = false, tags = {} }
-> { bucket_name, bucket_arn, bucket_id, sse_algorithm }
```

## Usage

```hcl
module "logs" {
  source      = "./modules/storage-bucket-private"
  name        = "example-logs-bucket"
  kms_key_arn = null # null なら SSE-S3、KMS キーの ARN を渡せば SSE-KMS
  tags        = { env = "prod" }
}
# module.logs.bucket_arn を IAM ポリシーの Resource に渡す
```

## Contract

- 公開アクセスブロックは 4 項目（`block_public_acls` / `block_public_policy` / `ignore_public_acls` / `restrict_public_buckets`）すべて `true`
- ACL は `BucketOwnerEnforced` で無効化される。オブジェクトの所有者は常にバケット所有者
- 保存時暗号化: `kms_key_arn` が `null` なら SSE-S3（`AES256`）、渡せば SSE-KMS（`aws:kms`）+ Bucket Key 有効。`sse_algorithm` 出力で確認できる
- 通信時暗号化: バケットポリシーが `aws:SecureTransport = false` のリクエストをバケットとオブジェクト（`arn/*`）の両方で `Deny` する
- `tags` はバケットに付く。付随リソース（public access block など）はタグを持たない
- `force_destroy` の既定は `false`。オブジェクトが残っていれば `destroy` は失敗する
- `name` は S3 の命名規則（3〜63 文字、小文字英数字・ハイフン・ドット）を validation で強制する。KMS 以外の ARN を `kms_key_arn` に渡すと弾く
- 冪等。同じ入力で再 apply しても差分は出ない

## Alternatives

- アカウント全体で公開を禁止するなら `aws_s3_account_public_access_block` を先に置く。バケット単位の設定はその上での多重防御
- 静的サイト配信で「CloudFront からだけ読める」バケットが要るときは `cdn-static-site` を使う（OAC 付きのバケットポリシーを追加する）
- 独自の SSE-KMS キーを作る側は `secret-kms-key`。このカードは既存キーの ARN を受け取るだけ

## Pitfalls

- バケット名はグローバル一意（全 AWS アカウント共通）。`name` を変えると再作成になり、中身は引き継がれない
- GCS / Azure Blob と違い、S3 はリージョンを provider 側で決める。module は provider ブロックを持たないので、呼び出し側の provider リージョンに作られる
- SSE-KMS はオブジェクトの読み書きごとに `kms:Decrypt` / `kms:GenerateDataKey` が要る。利用側のロールにキーの権限を忘れると `AccessDenied` になる
- `aws:SecureTransport` の Deny は `Principal: "*"` なので、バケット所有者自身も HTTP ではアクセスできない（意図どおり）
- バケットポリシーは公開アクセスブロックの後に付ける順序を `depends_on` で固定している。手で分けると競合エラーが出ることがある

## Test

`modules/storage-bucket-private/tests/storage-bucket-private.tftest.hcl`
