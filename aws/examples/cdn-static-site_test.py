"""カード cdn-static-site の Contract を検証するテスト"""

from __future__ import annotations

import importlib
import json

import pytest

mod = importlib.import_module("cdn-static-site")
static_site_distribution = mod.static_site_distribution

BUCKET = "example-static-site"
DOMAIN = "example-static-site.s3.us-east-1.amazonaws.com"
OAC = "E2ABCDEFGHIJKL"
CERT = "arn:aws:acm:us-east-1:123456789012:certificate/11111111-2222-3333-4444-555555555555"
ACCOUNT = "123456789012"
ALIASES = ["www.example.com", "example.com"]


def build(**overrides):
    kwargs = dict(
        bucket_name=BUCKET, bucket_domain=DOMAIN, oac_id=OAC, certificate_arn=CERT, aliases=ALIASES, account_id=ACCOUNT
    )
    kwargs.update(overrides)
    return static_site_distribution(**kwargs)


def test_snapshot():
    """出力の全体像（distribution_id を渡した完成形）"""
    out = build(distribution_id="E1234567890ABC")
    assert out == {
        "distribution_config": {
            "CallerReference": "example-static-site-static-site",
            "Comment": "static site: www.example.com",
            "Enabled": True,
            "DefaultRootObject": "index.html",
            "Aliases": {"Quantity": 2, "Items": ["www.example.com", "example.com"]},
            "Origins": {
                "Quantity": 1,
                "Items": [
                    {
                        "Id": "s3-example-static-site",
                        "DomainName": DOMAIN,
                        "OriginAccessControlId": OAC,
                        "S3OriginConfig": {"OriginAccessIdentity": ""},
                    }
                ],
            },
            "DefaultCacheBehavior": {
                "TargetOriginId": "s3-example-static-site",
                "ViewerProtocolPolicy": "redirect-to-https",
                "AllowedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"], "CachedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]}},
                "Compress": True,
                "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",
            },
            "PriceClass": "PriceClass_100",
            "ViewerCertificate": {
                "ACMCertificateArn": CERT,
                "SSLSupportMethod": "sni-only",
                "MinimumProtocolVersion": "TLSv1.2_2021",
            },
            "HttpVersion": "http2and3",
            "IsIPV6Enabled": True,
        },
        "bucket_policy": {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Sid": "AllowCloudFrontServicePrincipalReadOnly",
                    "Effect": "Allow",
                    "Principal": {"Service": "cloudfront.amazonaws.com"},
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::example-static-site/*",
                    "Condition": {"StringEquals": {"AWS:SourceArn": "arn:aws:cloudfront::123456789012:distribution/E1234567890ABC"}},
                }
            ],
        },
    }
    json.dumps(out)


def test_https_only_and_modern_tls():
    """HTTP は HTTPS へリダイレクト、TLS 1.2 (2021) 以上、SNI"""
    cfg = build()["distribution_config"]
    assert cfg["DefaultCacheBehavior"]["ViewerProtocolPolicy"] == "redirect-to-https"
    assert cfg["ViewerCertificate"]["MinimumProtocolVersion"] == "TLSv1.2_2021"
    assert cfg["ViewerCertificate"]["SSLSupportMethod"] == "sni-only"
    assert "CloudFrontDefaultCertificate" not in cfg["ViewerCertificate"]


def test_origin_uses_oac_and_read_only_methods():
    """オリジンは OAC 付きの S3（OAI は空）。許可メソッドは GET / HEAD のみ"""
    cfg = build()["distribution_config"]
    (origin,) = cfg["Origins"]["Items"]
    assert origin["OriginAccessControlId"] == OAC
    assert origin["S3OriginConfig"] == {"OriginAccessIdentity": ""}
    assert "CustomOriginConfig" not in origin
    assert cfg["DefaultCacheBehavior"]["AllowedMethods"]["Items"] == ["GET", "HEAD"]
    assert cfg["DefaultCacheBehavior"]["TargetOriginId"] == origin["Id"]


def test_bucket_policy_allows_only_get_object_from_cloudfront():
    """バケットポリシーは cloudfront.amazonaws.com の s3:GetObject のみ。distribution_id 無しなら同アカウントの ArnLike"""
    policy = build()["bucket_policy"]
    (stmt,) = policy["Statement"]
    assert stmt["Effect"] == "Allow"
    assert stmt["Action"] == "s3:GetObject"
    assert stmt["Principal"] == {"Service": "cloudfront.amazonaws.com"}
    assert stmt["Resource"] == "arn:aws:s3:::example-static-site/*"
    assert stmt["Condition"] == {"ArnLike": {"AWS:SourceArn": "arn:aws:cloudfront::123456789012:distribution/*"}}
    assert "ListBucket" not in json.dumps(policy)


def test_price_class_and_caller_reference_overrides():
    """price_class は 3 種類のみ。caller_reference は差し替え可能"""
    for ok in ("PriceClass_100", "PriceClass_200", "PriceClass_All"):
        assert build(price_class=ok)["distribution_config"]["PriceClass"] == ok
    with pytest.raises(ValueError):
        build(price_class="PriceClass_300")
    assert build(caller_reference="deploy-2026-09-18")["distribution_config"]["CallerReference"] == "deploy-2026-09-18"


def test_certificate_must_be_in_us_east_1():
    """us-east-1 以外の ACM 証明書、ACM 以外の ARN は ValueError"""
    with pytest.raises(ValueError):
        build(certificate_arn="arn:aws:acm:ap-northeast-1:123456789012:certificate/11111111-2222-3333-4444-555555555555")
    with pytest.raises(ValueError):
        build(certificate_arn="arn:aws:iam::123456789012:server-certificate/x")


def test_rejects_website_endpoint_and_mismatched_domain():
    """website エンドポイントや別バケットのドメインは ValueError"""
    with pytest.raises(ValueError):
        build(bucket_domain="example-static-site.s3-website-us-east-1.amazonaws.com")
    with pytest.raises(ValueError):
        build(bucket_domain="other-bucket.s3.us-east-1.amazonaws.com")


def test_rejects_invalid_aliases_oac_bucket_distribution():
    """aliases 空・重複・不正、OAC / バケット名 / distribution_id / account_id の形式違いは ValueError"""
    with pytest.raises(ValueError):
        build(aliases=[])
    with pytest.raises(ValueError):
        build(aliases=["www.example.com", "www.example.com"])
    with pytest.raises(ValueError):
        build(aliases=["https://www.example.com"])
    with pytest.raises(ValueError):
        build(oac_id="oac-1")
    with pytest.raises(ValueError):
        build(bucket_name="Example_Bucket", bucket_domain="Example_Bucket.s3.us-east-1.amazonaws.com")
    with pytest.raises(ValueError):
        build(distribution_id="1234")
    with pytest.raises(ValueError):
        build(account_id="12")
    with pytest.raises(ValueError):
        build(default_root_object="/index.html")
