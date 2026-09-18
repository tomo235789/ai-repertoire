---
id: cdn-static-site
lang: terraform
title: 静的サイトを CDN 経由で HTTPS 配信する
tags: [静的サイト, CDN, HTTPS, 配信, 非公開バケット, cloudfront, oac, static-site]
lib: hashicorp/aws
fn: aws_cloudfront_distribution
since: "5.0"
verified: 2026-09-18
status: public
---

非公開のままの S3 バケットを CloudFront から HTTPS で配信する。OAC（Origin Access Control）で配信元だけに読み取りを許し、HTTP は HTTPS へ転送する。

## Signature

```hcl
module "site" { source, bucket_name, bucket_regional_domain_name, certificate_arn, aliases, default_root_object?, price_class?, tags? }
# -> { distribution_id, distribution_arn, domain_name, origin_access_control_id }
```

## Usage

```hcl
module "site" {
  source                      = "./modules/cdn-static-site"
  bucket_name                 = module.assets.bucket_name # storage-bucket-private で作った非公開バケット
  bucket_regional_domain_name = module.assets.bucket_regional_domain_name
  certificate_arn             = "arn:aws:acm:us-east-1:123456789012:certificate/12345678-1234-1234-1234-123456789012"
  aliases                     = ["static.example.com"]
  tags                        = { env = "prod" }
}
# => domain_name を DNS の別名レコードの向き先にする
```

## Contract

- ビューワーは HTTPS を強制される。`viewer_protocol_policy` は `redirect-to-https` で、HTTP は 301 で HTTPS へ転送される
- TLS は 1.2 以上（`minimum_protocol_version = "TLSv1.2_2021"`）、証明書は SNI で提示する
- 配信元は OAC 経由でのみ読まれる。`signing_behavior = "always"` / `origin_access_control_origin_type = "s3"` で、バケットを公開設定に戻す必要がない
- バケットポリシーは Statement 1 つだけで、許可するのは `s3:GetObject` のみ、Resource はそのバケットのオブジェクト（`arn:aws:s3:::<bucket>/*`）のみ、`AWS:SourceArn` 条件でこの配信の ARN に限定する
- `aliases` はそのまま配信に渡る。`default_root_object` の既定は `index.html`、`price_class` の既定は `PriceClass_100`
- `tags` は配信に付く
- `certificate_arn` が us-east-1 以外、`aliases` が空、`price_class` が既知の 3 値以外なら plan が失敗する
- キャッシュはマネージドポリシー CachingOptimized（`658327ea-f89d-4fab-a63d-7e88639e58f6`）を使う。TTL を自分で決めたいなら `cache_policy_id` を差し替える
- このモジュールはバケットも証明書も DNS レコードも作らない。作成済みのものを受け取るだけなので、適用順は バケット → 証明書 → このモジュール → DNS になる

## Alternatives

- SDK や CloudFormation に渡す設定を組み立てるなら `aws/examples/cdn-static-site.py`（同じ ID の純粋関数）
- 署名付き URL や Cookie で配信を制限するなら、OAC に加えて CloudFront の trusted key group を設定する
- 動的な処理を挟むなら CloudFront Functions か Lambda@Edge。静的配信だけならどちらも要らない

## Pitfalls

- **ACM 証明書は us-east-1 のものしか使えない**。他リージョンの証明書を渡すと validation で弾かれる（バケットや配信のリージョンとは無関係）
- `aliases` に入れた名前は証明書がカバーしている必要がある。カバーしていないと apply が失敗する
- OAC は旧来の OAI（Origin Access Identity）と別物。OAI から移行するときはバケットポリシーも書き換える
- 配信の作成・更新は反映に数分から十数分かかる。`terraform apply` が返ってもエッジへ行き渡るまで待つ必要がある
- `default_root_object` はディストリビューションのルート（`/`）にしか効かない。サブディレクトリの `index.html` を返したいなら CloudFront Functions で書き換える

## Test

`modules/cdn-static-site/tests/cdn-static-site.tftest.hcl`
