"""カード cdn-static-site: 静的サイトを CDN 経由で HTTPS 配信する構成を組み立てる純粋関数。

Compute Engine のバックエンドバケット・URL マップ・ターゲットプロキシ・転送ルールに
渡すリソースを返す。API は呼ばない。
"""

from __future__ import annotations

import re

_NAME_RE = re.compile(r"^[a-z]([-a-z0-9]{0,61}[a-z0-9])?$")
_DOMAIN_RE = re.compile(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$")
# Cloud Storage のバケット名。全体 222 文字、ドットで区切った各要素は 63 文字まで。
# goog 接頭辞、google の類似表記、IP アドレス形式は使えない
_BUCKET_LABEL_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{1,61}[a-z0-9]$|^[a-z0-9]{3}$")
_IPV4_LIKE_RE = re.compile(r"^\d{1,3}(\.\d{1,3}){3}$")
# o と 0、l と 1 を入れ替えた表記も拒否される
_GOOGLE_LIKE_RE = re.compile(r"g[o0]{2}g[l1]e")


def _is_valid_bucket_name(name: str) -> bool:
    """Cloud Storage が受け付けるバケット名かを判定する"""
    if not 3 <= len(name) <= 222 or ".." in name:
        return False
    if name.startswith("goog") or _GOOGLE_LIKE_RE.search(name) or _IPV4_LIKE_RE.match(name):
        return False
    return all(_BUCKET_LABEL_RE.match(label) for label in name.split("."))

CACHE_MODES = ("CACHE_ALL_STATIC", "USE_ORIGIN_HEADERS", "FORCE_CACHE_ALL")
# TLS の最低バージョンを決めるプロファイル
SSL_POLICY = {"profile": "MODERN", "minTlsVersion": "TLS_1_2"}


def static_site_config(
    name: str,
    bucket_name: str,
    domains: tuple[str, ...] | list[str],
    *,
    cache_mode: str = "CACHE_ALL_STATIC",
    default_ttl_seconds: int = 3600,
    max_ttl_seconds: int = 86400,
    client_ttl_seconds: int = 300,
    enable_negative_caching: bool = True,
    serve_while_stale_seconds: int = 86400,
) -> dict:
    """バケットを CDN 越しに HTTPS で配るための構成を返す。

    Args:
        name: 各リソースの名前の元になる文字列
        bucket_name: 配信元のバケット名
        domains: 証明書を発行するドメイン。1 件以上
        cache_mode: CACHE_MODES のいずれか
        default_ttl_seconds: 既定の保持時間
        max_ttl_seconds: 保持時間の上限。既定以上
        client_ttl_seconds: ブラウザ側の保持時間。既定以下
        enable_negative_caching: 404 などもキャッシュするか
        serve_while_stale_seconds: 元が落ちたとき古い内容を出し続ける時間

    Returns:
        backend_bucket / url_map / ssl_certificate / ssl_policy / target_proxy /
        forwarding_rule と、HTTP から寄せるための http_redirect_url_map /
        http_target_proxy / http_forwarding_rule を持つ dict

    Raises:
        ValueError: 名前やドメインの形式違い、ドメインが空、未知のキャッシュモード、
            保持時間の大小関係が逆の場合
    """
    if not _NAME_RE.match(name):
        raise ValueError(f"名前の形式が不正: {name!r}")
    if not _is_valid_bucket_name(bucket_name):
        raise ValueError(f"バケット名の形式が不正: {bucket_name!r}")
    unique_domains = sorted(set(domains))
    if not unique_domains:
        raise ValueError("domains は 1 件以上必要")
    for domain in unique_domains:
        if not _DOMAIN_RE.match(domain):
            raise ValueError(f"ドメインの形式が不正: {domain!r}")
    if cache_mode not in CACHE_MODES:
        raise ValueError(f"キャッシュモードは {CACHE_MODES} のいずれか: {cache_mode!r}")
    if max_ttl_seconds < default_ttl_seconds:
        raise ValueError(
            f"上限は既定以上にする: {max_ttl_seconds} < {default_ttl_seconds}"
        )
    if client_ttl_seconds > default_ttl_seconds:
        raise ValueError(
            f"ブラウザ側の保持は既定以下にする: {client_ttl_seconds} > {default_ttl_seconds}"
        )

    backend_bucket = {
        "name": f"{name}-backend",
        "bucketName": bucket_name,
        "enableCdn": True,
        "cdnPolicy": {
            "cacheMode": cache_mode,
            "defaultTtl": default_ttl_seconds,
            "maxTtl": max_ttl_seconds,
            "clientTtl": client_ttl_seconds,
            "negativeCaching": enable_negative_caching,
            "serveWhileStale": serve_while_stale_seconds,
            # バックエンドバケットのキャッシュキーは既定で Cloud Storage 固有の
            # クエリパラメータを含む。whitelist はそこへ足す指定なので、
            # 追加したいパラメータが無ければ空のまま
            "cacheKeyPolicy": {"includeHttpHeaders": [], "queryStringWhitelist": []},
        },
    }

    return {
        "backend_bucket": backend_bucket,
        "url_map": {
            "name": f"{name}-url-map",
            # リソース参照は部分 URL で渡す。裸の名前では解決できない
            "defaultService": f"global/backendBuckets/{name}-backend",
        },
        "ssl_certificate": {
            "name": f"{name}-cert",
            "type": "MANAGED",
            "managed": {"domains": unique_domains},
        },
        "ssl_policy": {"name": f"{name}-ssl-policy", **SSL_POLICY},
        "target_proxy": {
            "name": f"{name}-https-proxy",
            "urlMap": f"global/urlMaps/{name}-url-map",
            "sslCertificates": [f"global/sslCertificates/{name}-cert"],
            "sslPolicy": f"global/sslPolicies/{name}-ssl-policy",
        },
        "forwarding_rule": {
            "name": f"{name}-https",
            "target": f"global/targetHttpsProxies/{name}-https-proxy",
            "portRange": "443",
            "loadBalancingScheme": "EXTERNAL_MANAGED",
        },
        # 平文で来たアクセスは HTTPS へ寄せる。URL マップだけでは受け口が無いので、
        # 専用のプロキシとポート 80 の転送ルールもあわせて作る
        "http_redirect_url_map": {
            "name": f"{name}-http-redirect",
            "defaultUrlRedirect": {
                "httpsRedirect": True,
                "redirectResponseCode": "MOVED_PERMANENTLY_DEFAULT",
                "stripQuery": False,
            },
        },
        "http_target_proxy": {
            "name": f"{name}-http-proxy",
            "urlMap": f"global/urlMaps/{name}-http-redirect",
        },
        "http_forwarding_rule": {
            "name": f"{name}-http",
            "target": f"global/targetHttpProxies/{name}-http-proxy",
            "portRange": "80",
            "loadBalancingScheme": "EXTERNAL_MANAGED",
        },
    }
