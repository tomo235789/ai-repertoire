"""カード cdn-static-site の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("cdn-static-site.py")
    spec = importlib.util.spec_from_file_location("cdn_static_site", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


static_site_config = _load().static_site_config


def _cfg(**kw):
    return static_site_config("example-site", "example-bucket", ["www.example.com"], **kw)


def test_cdn_enabled_on_backend():
    """バックエンドバケットで CDN を有効にする"""
    backend = _cfg()["backend_bucket"]
    assert backend["enableCdn"] is True
    assert backend["bucketName"] == "example-bucket"
    assert backend["cdnPolicy"]["cacheMode"] == "CACHE_ALL_STATIC"


def test_https_redirect_and_tls_policy():
    """平文は HTTPS へ寄せ、TLS 1.2 以上に絞る"""
    cfg = _cfg()
    assert cfg["http_redirect_url_map"]["defaultUrlRedirect"]["httpsRedirect"] is True
    assert cfg["ssl_policy"]["minTlsVersion"] == "TLS_1_2"
    assert cfg["ssl_policy"]["profile"] == "MODERN"


def test_http_frontend_is_complete():
    """HTTP の受け口はプロキシと 80 番の転送ルールまで揃える"""
    cfg = _cfg()
    assert cfg["http_target_proxy"]["urlMap"] == (
        f"global/urlMaps/{cfg['http_redirect_url_map']['name']}"
    )
    assert cfg["http_forwarding_rule"]["target"] == (
        f"global/targetHttpProxies/{cfg['http_target_proxy']['name']}"
    )
    assert cfg["http_forwarding_rule"]["portRange"] == "80"


def test_managed_certificate_domains_sorted():
    """証明書のドメインは重複を除いて名前順"""
    cfg = static_site_config(
        "example-site", "example-bucket", ["www.example.com", "example.com", "example.com"]
    )
    assert cfg["ssl_certificate"]["managed"]["domains"] == ["example.com", "www.example.com"]
    assert cfg["ssl_certificate"]["type"] == "MANAGED"


def test_resources_are_wired_by_partial_url():
    """リソース参照は部分 URL。裸の名前では Compute Engine が解決できない"""
    cfg = _cfg()
    assert cfg["url_map"]["defaultService"] == (
        f"global/backendBuckets/{cfg['backend_bucket']['name']}"
    )
    assert cfg["target_proxy"]["urlMap"] == f"global/urlMaps/{cfg['url_map']['name']}"
    assert cfg["target_proxy"]["sslCertificates"] == [
        f"global/sslCertificates/{cfg['ssl_certificate']['name']}"
    ]
    assert cfg["target_proxy"]["sslPolicy"] == (
        f"global/sslPolicies/{cfg['ssl_policy']['name']}"
    )
    assert cfg["forwarding_rule"]["target"] == (
        f"global/targetHttpsProxies/{cfg['target_proxy']['name']}"
    )


def test_cache_key_ignores_query_string():
    """クエリ文字列とヘッダーでキャッシュを分けない"""
    policy = _cfg()["backend_bucket"]["cdnPolicy"]["cacheKeyPolicy"]
    assert policy == {"includeHttpHeaders": [], "queryStringWhitelist": []}


def test_ttl_relationships():
    """上限は既定以上、ブラウザ側は既定以下"""
    with pytest.raises(ValueError, match="上限は既定以上"):
        _cfg(default_ttl_seconds=3600, max_ttl_seconds=60)
    with pytest.raises(ValueError, match="ブラウザ側"):
        _cfg(default_ttl_seconds=60, client_ttl_seconds=3600)


def test_serve_while_stale():
    """元が落ちても古い内容を出し続ける時間を持つ"""
    assert _cfg()["backend_bucket"]["cdnPolicy"]["serveWhileStale"] == 86400


def test_invalid_inputs():
    """名前・ドメイン・キャッシュモードの不正は ValueError"""
    with pytest.raises(ValueError):
        static_site_config("Example_Site", "example-bucket", ["www.example.com"])
    with pytest.raises(ValueError):
        static_site_config("example-site", "example-bucket", [])
    with pytest.raises(ValueError):
        static_site_config("example-site", "example-bucket", ["www_example_com"])
    with pytest.raises(ValueError):
        _cfg(cache_mode="ALWAYS")


def test_reserved_bucket_names_rejected():
    """IP アドレス形式と goog 接頭辞のバケット名は Cloud Storage が拒否する"""
    for bad in ("192.168.5.4", "goog-site", "my-google-site"):
        with pytest.raises(ValueError, match="バケット名"):
            static_site_config("example-site", bad, ["www.example.com"])


def test_dotted_bucket_names_allowed():
    """ドットで区切った各要素が 63 文字以内なら、全体が 63 文字を超えてもよい"""
    long_dotted = ".".join(["a" * 60] * 3)
    assert static_site_config("example-site", long_dotted, ["www.example.com"])


def test_google_lookalike_bucket_names_rejected():
    """google の類似表記も Cloud Storage は拒否する"""
    for bad in ("g00gle-site", "goog1e-site", "goog-site"):
        with pytest.raises(ValueError, match="バケット名"):
            static_site_config("example-site", bad, ["www.example.com"])


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = _cfg()
    assert a == _cfg()
    assert json.loads(json.dumps(a)) == a
