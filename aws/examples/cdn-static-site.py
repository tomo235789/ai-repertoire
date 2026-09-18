"""カード cdn-static-site: 非公開 S3 バケットを OAC 経由で CloudFront から HTTPS 配信する

cloudfront.create_distribution に渡す DistributionConfig（dict）と、S3 バケットに設定するバケットポリシー（dict）を返す。
"""

from __future__ import annotations

import re
from typing import Any, Sequence

_BUCKET_NAME_RE = re.compile(r"^(?!\d+\.\d+\.\d+\.\d+$)[a-z0-9](?:[a-z0-9.-]{1,61})[a-z0-9]$")
_ACM_US_EAST_1_ARN_RE = re.compile(r"^arn:aws:acm:us-east-1:\d{12}:certificate/[0-9a-f-]{36}$")
_ACCOUNT_RE = re.compile(r"^\d{12}$")
_HOSTNAME_RE = re.compile(r"^(?:\*\.)?(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$")
_OAC_ID_RE = re.compile(r"^[A-Z0-9]{8,32}$")
_DISTRIBUTION_ID_RE = re.compile(r"^E[A-Z0-9]{8,20}$")

PRICE_CLASSES = ("PriceClass_100", "PriceClass_200", "PriceClass_All")
# CloudFront のマネージドキャッシュポリシー CachingOptimized
CACHING_OPTIMIZED_POLICY_ID = "658327ea-f89d-4fab-a63d-7e88639e58f6"
MINIMUM_PROTOCOL_VERSION = "TLSv1.2_2021"


def _origin_id(bucket_name: str) -> str:
    return f"s3-{bucket_name}"


def static_site_distribution(
    bucket_name: str,
    bucket_domain: str,
    oac_id: str,
    certificate_arn: str,
    aliases: Sequence[str],
    price_class: str = "PriceClass_100",
    *,
    account_id: str,
    distribution_id: str | None = None,
    default_root_object: str = "index.html",
    caller_reference: str | None = None,
    comment: str | None = None,
) -> dict[str, Any]:
    """静的サイト配信の DistributionConfig とバケットポリシーを返す。

    :param bucket_name: 配信元の非公開 S3 バケット名
    :param bucket_domain: バケットの REST エンドポイント（`<bucket>.s3.<region>.amazonaws.com`）。website エンドポイントは不可
    :param oac_id: 作成済みの Origin Access Control の ID
    :param certificate_arn: us-east-1 の ACM 証明書 ARN（CloudFront は us-east-1 の証明書しか使えない）
    :param aliases: 配信するドメイン名（1 つ以上。証明書がカバーしていること）
    :param price_class: PriceClass_100 / PriceClass_200 / PriceClass_All
    :param account_id: バケットポリシーの aws:SourceArn に使うアカウント ID
    :param distribution_id: 作成後に判明するディストリビューション ID。None なら同アカウントの任意のディストリビューション（ArnLike）に緩める
    :param caller_reference: create_distribution の冪等キー。None なら bucket_name から決める
    """
    if not _BUCKET_NAME_RE.match(bucket_name):
        raise ValueError(f"バケット名が不正: {bucket_name!r}")
    if not bucket_domain.startswith(f"{bucket_name}.s3") or "s3-website" in bucket_domain or "website" in bucket_domain:
        raise ValueError(
            f"bucket_domain は {bucket_name}.s3.<region>.amazonaws.com の REST エンドポイント（website エンドポイントは OAC 不可）: {bucket_domain!r}"
        )
    if not _OAC_ID_RE.match(oac_id):
        raise ValueError(f"OAC の ID ではない: {oac_id!r}")
    if not _ACM_US_EAST_1_ARN_RE.match(certificate_arn):
        raise ValueError(f"CloudFront の証明書は us-east-1 の ACM 証明書 ARN: {certificate_arn!r}")
    names = list(aliases)
    if not names:
        raise ValueError("aliases は 1 つ以上必要（証明書付きの配信には独自ドメインが要る）")
    if len(set(names)) != len(names):
        raise ValueError("aliases に重複がある")
    for host in names:
        if not _HOSTNAME_RE.match(host):
            raise ValueError(f"ドメイン名が不正: {host!r}")
    if price_class not in PRICE_CLASSES:
        raise ValueError(f"price_class は {PRICE_CLASSES} のいずれか: {price_class!r}")
    if not _ACCOUNT_RE.match(account_id):
        raise ValueError(f"account_id は 12 桁の数字: {account_id!r}")
    if distribution_id is not None and not _DISTRIBUTION_ID_RE.match(distribution_id):
        raise ValueError(f"ディストリビューション ID ではない: {distribution_id!r}")
    if not default_root_object or "/" in default_root_object:
        raise ValueError(f"default_root_object はスラッシュ無しのファイル名: {default_root_object!r}")

    origin_id = _origin_id(bucket_name)
    distribution_config: dict[str, Any] = {
        "CallerReference": caller_reference or f"{bucket_name}-static-site",
        "Comment": comment or f"static site: {names[0]}",
        "Enabled": True,
        "DefaultRootObject": default_root_object,
        "Aliases": {"Quantity": len(names), "Items": names},
        "Origins": {
            "Quantity": 1,
            "Items": [
                {
                    "Id": origin_id,
                    "DomainName": bucket_domain,
                    "OriginAccessControlId": oac_id,
                    "S3OriginConfig": {"OriginAccessIdentity": ""},
                }
            ],
        },
        "DefaultCacheBehavior": {
            "TargetOriginId": origin_id,
            "ViewerProtocolPolicy": "redirect-to-https",
            "AllowedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"], "CachedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]}},
            "Compress": True,
            "CachePolicyId": CACHING_OPTIMIZED_POLICY_ID,
        },
        "PriceClass": price_class,
        "ViewerCertificate": {
            "ACMCertificateArn": certificate_arn,
            "SSLSupportMethod": "sni-only",
            "MinimumProtocolVersion": MINIMUM_PROTOCOL_VERSION,
        },
        "HttpVersion": "http2and3",
        "IsIPV6Enabled": True,
    }

    if distribution_id:
        condition = {"StringEquals": {"AWS:SourceArn": f"arn:aws:cloudfront::{account_id}:distribution/{distribution_id}"}}
    else:
        condition = {"ArnLike": {"AWS:SourceArn": f"arn:aws:cloudfront::{account_id}:distribution/*"}}
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Sid": "AllowCloudFrontServicePrincipalReadOnly",
                "Effect": "Allow",
                "Principal": {"Service": "cloudfront.amazonaws.com"},
                "Action": "s3:GetObject",
                "Resource": f"arn:aws:s3:::{bucket_name}/*",
                "Condition": condition,
            }
        ],
    }
    return {"distribution_config": distribution_config, "bucket_policy": bucket_policy}
