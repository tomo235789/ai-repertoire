"""カード cdn-static-site: 静的サイトを CDN 経由で HTTPS 配信する構成を組み立てる純粋関数。

`azure-mgmt-cdn` の Front Door（Standard/Premium）のオリジン・ルート・規則に
渡すプロパティを返す。API は呼ばない。
"""

from __future__ import annotations

import re

_HOST_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$")

# 既定でキャッシュする拡張子と秒数
DEFAULT_CACHE_SECONDS = 86400
# HTML は短く持つ。差し替えが反映されないと事故になる
HTML_CACHE_SECONDS = 60

SECURITY_HEADERS: dict[str, str] = {
    "Strict-Transport-Security": "max-age=63072000; includeSubDomains; preload",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Content-Security-Policy": "default-src 'self'",
}


def static_site_config(
    origin_host: str,
    *,
    origin_group_id: str,
    custom_domain_id: str | None = None,
    cache_seconds: int = DEFAULT_CACHE_SECONDS,
    html_cache_seconds: int = HTML_CACHE_SECONDS,
    compress: bool = True,
) -> dict:
    """静的サイトのオリジンとルートと応答ヘッダーの設定を返す。

    Args:
        origin_host: 配信元のホスト名。ストレージの静的 Web サイトなど
        origin_group_id: オリジングループの ARM リソース ID
        custom_domain_id: 独自ドメイン（AFDDomain）の ARM リソース ID。
            省略すると Front Door の既定ホストだけ
        cache_seconds: 静的ファイルのキャッシュ秒数
        html_cache_seconds: HTML のキャッシュ秒数。静的ファイルより短くする
        compress: 圧縮を有効にするか

    Returns:
        origin / route / response_headers / security_policy を持つ dict

    Raises:
        ValueError: ホスト名の形式違い、オリジングループか独自ドメインが
            ARM リソース ID でない、キャッシュ秒数が負、
            HTML のキャッシュが静的ファイルより長い場合
    """
    if not _HOST_RE.match(origin_host):
        raise ValueError(f"オリジンのホスト名の形式が不正: {origin_host!r}")
    if custom_domain_id is not None and not custom_domain_id.startswith("/subscriptions/"):
        raise ValueError(
            f"独自ドメインは AFDDomain の ARM リソース ID で指定する: {custom_domain_id!r}"
        )
    if not origin_group_id.startswith("/subscriptions/"):
        raise ValueError(
            f"オリジングループは ARM リソース ID で指定する: {origin_group_id!r}"
        )
    if cache_seconds < 0 or html_cache_seconds < 0:
        raise ValueError("キャッシュ秒数は 0 以上")
    if html_cache_seconds > cache_seconds:
        raise ValueError(
            "HTML のキャッシュは静的ファイル以下にする: "
            f"{html_cache_seconds} > {cache_seconds}"
        )

    origin = {
        "hostName": origin_host,
        "originHostHeader": origin_host,
        "httpPort": 80,
        "httpsPort": 443,
        "priority": 1,
        "weight": 1000,
        # オリジンへも HTTPS で繋ぎ、公開アクセスはプライベートリンクで塞げるようにする
        "enforceCertificateNameCheck": True,
    }

    route = {
        "originGroup": {"id": origin_group_id},
        "supportedProtocols": ["Http", "Https"],
        "patternsToMatch": ["/*"],
        # 平文でのアクセスは HTTPS へ寄せる
        "httpsRedirect": "Enabled",
        "forwardingProtocol": "HttpsOnly",
        "linkToDefaultDomain": "Enabled" if custom_domain_id is None else "Disabled",
        "cacheConfiguration": {
            "queryStringCachingBehavior": "IgnoreQueryString",
            "compressionSettings": {
                "isCompressionEnabled": compress,
                "contentTypesToCompress": [
                    "application/javascript",
                    "application/json",
                    "image/svg+xml",
                    "text/css",
                    "text/html",
                ],
            },
        },
    }
    if custom_domain_id is not None:
        route["customDomains"] = [{"id": custom_domain_id}]

    return {
        "origin": origin,
        "route": route,
        "response_headers": dict(sorted(SECURITY_HEADERS.items())),
        "cache_rules": [
            {
                "name": "html-short-cache",
                "match": {"extensions": ["html"]},
                "cache_duration_seconds": html_cache_seconds,
            },
            {
                "name": "asset-long-cache",
                "match": {"extensions": ["css", "js", "png", "svg", "webp", "woff2"]},
                "cache_duration_seconds": cache_seconds,
            },
        ],
        "minimumTlsVersion": "TLS1_2",
    }
