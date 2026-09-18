---
id: cdn-static-site
lang: aws
title: 静的サイトを CDN 経由で HTTPS 配信する
tags: [CloudFront, OAC, S3, 静的サイト, HTTPS, CloudFront-distribution, origin-access-control, static-site]
lib: aws.cloudfront
fn: static_site_distribution
since: "2024"
verified: 2026-09-18
status: public
---

非公開 S3 バケットを OAC（Origin Access Control）経由で CloudFront に繋ぎ、独自ドメインで HTTPS 配信する DistributionConfig とバケットポリシーの 2 つをセットで組み立てる。OAI の代わりに OAC を使うのが前提。

## Signature

```python
def static_site_distribution(bucket_name: str, bucket_domain: str, oac_id: str, certificate_arn: str, aliases: Sequence[str], price_class: str = "PriceClass_100", *, account_id: str, distribution_id: str | None = None, default_root_object: str = "index.html", caller_reference: str | None = None, comment: str | None = None) -> dict[str, Any]
```

## Usage

```python
from cdn_static_site import static_site_distribution  # examples/cdn-static-site.py をコピー

out = static_site_distribution(
    bucket_name="my-static", bucket_domain="my-static.s3.us-east-1.amazonaws.com",
    oac_id="E2ABCDEFGHIJKL", certificate_arn=CERT, aliases=["www.example.com"],
    account_id="123456789012"
)
cf.create_distribution(DistributionConfig=out["distribution_config"])  # create → OAC 付き S3 オリジン
s3.put_bucket_policy(Bucket="my-static", Policy=json.dumps(out["bucket_policy"]))  # CloudFront の読み取りを許可
```

## Contract

- `distribution_config` は HTTPS のみ。ViewerProtocolPolicy は `redirect-to-https`（HTTP を拒否）
- ViewerCertificate に ACM us-east-1 証明書を設定。TLS バージョンは最低 `TLSv1.2_2021`、SNI 専用
- オリビンは OAC 付きの S3。OAI（Origin Access Identity）は空文字。CustomOriginConfig を含まない
- AllowedMethods は GET / HEAD のみ（キャッシュ対象）。Compress=True で gzip/brotli 圧縮有効
- CachePolicyId はマネージド `CachingOptimized`（既定 TTL とクエリ文字列扱いが最適化済み）
- バケットポリシーは CloudFront Service Principal の `s3:GetObject` のみ。`ListBucket` を含まない
- `distribution_id` 未指定なら条件を緩める（`ArnLike` + `*`）。指定されれば `StringEquals` に厳密化
- PriceClass は `PriceClass_100` / `PriceClass_200` / `PriceClass_All` のみ。既定は 100

## Alternatives

- Terraform resource `terraform/cloudfront_distribution` / `terraform/s3_bucket_policy`（同じロジックを HCL で記述）
- CloudFormation `AWS::CloudFront::Distribution` + `AWS::S3::BucketPolicy` リソース

## Pitfalls

- CloudFront の証明書 ARN は **us-east-1** の ACM でのみ発行可能。リージョンが違うと受け付けない
- バケットドメインは REST エンドポイント（`<bucket>.s3.<region>.amazonaws.com`）を使う。website エンドポイントでは OAC が動作しない
- `default_root_object` に `/index.html` のように先頭にスラッシュが付くと invalid。ファイル名のみを渡す
- バケットポリシーの `Condition.ArnLike` は作成時にディストリビューション ID が判明していない場合に使う。確定後は `StringEquals` に交換する

## Test

`examples/cdn-static-site_test.py`
