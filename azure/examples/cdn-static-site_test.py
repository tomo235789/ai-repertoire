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


_mod = _load()
static_site_config = _mod.static_site_config
SECURITY_HEADERS = _mod.SECURITY_HEADERS

ORIGIN = "examplestorage.z11.web.core.windows.net"
ORIGIN_GROUP = (
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
    "/providers/Microsoft.Cdn/profiles/example-fd/originGroups/static"
)


def _cfg(**kw):
    kwargs = {"origin_group_id": ORIGIN_GROUP}
    kwargs.update(kw)
    return static_site_config(ORIGIN, **kwargs)


def _cfg2(origin_host, **kw):
    kwargs = {"origin_group_id": ORIGIN_GROUP}
    kwargs.update(kw)
    return static_site_config(origin_host, **kwargs)


def test_origin_group_is_arm_id():
    """オリジングループは ARM リソース ID で参照する"""
    assert _cfg()["route"]["originGroup"] == {"id": ORIGIN_GROUP}
    with pytest.raises(ValueError, match="オリジングループ"):
        static_site_config(ORIGIN, origin_group_id="static")


def test_https_is_enforced():
    """平文は HTTPS へ寄せ、オリジンへも HTTPS で繋ぐ"""
    cfg = _cfg()
    assert cfg["route"]["httpsRedirect"] == "Enabled"
    assert cfg["route"]["forwardingProtocol"] == "HttpsOnly"
    assert cfg["minimumTlsVersion"] == "TLS1_2"
    assert cfg["origin"]["enforceCertificateNameCheck"] is True


def test_security_headers():
    """応答ヘッダーは名前順で、HSTS と nosniff が入る"""
    headers = _cfg()["response_headers"]
    assert list(headers) == sorted(SECURITY_HEADERS)
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["Strict-Transport-Security"].startswith("max-age=63072000")


def test_html_cached_shorter_than_assets():
    """HTML は短く、資産は長くキャッシュする"""
    rules = {r["name"]: r for r in _cfg()["cache_rules"]}
    assert rules["html-short-cache"]["cache_duration_seconds"] == 60
    assert rules["asset-long-cache"]["cache_duration_seconds"] == 86400


def test_custom_domain_disables_default_domain():
    """独自ドメインを付けたら既定ドメインへの紐付けは外す"""
    cfg = _cfg()
    assert cfg["route"]["linkToDefaultDomain"] == "Enabled"
    assert "customDomains" not in cfg["route"]
    cfg = _cfg(custom_domain="www.example.com")
    assert cfg["route"]["linkToDefaultDomain"] == "Disabled"
    assert cfg["route"]["customDomains"] == [{"hostName": "www.example.com"}]


def test_compression_can_be_disabled():
    """圧縮は切れる"""
    settings = _cfg(compress=False)["route"]["cacheConfiguration"]
    assert settings["compressionSettings"]["isCompressionEnabled"] is False


def test_query_string_ignored():
    """クエリ文字列でキャッシュを分けない"""
    cache = _cfg()["route"]["cacheConfiguration"]
    assert cache["queryStringCachingBehavior"] == "IgnoreQueryString"


def test_html_cache_must_not_exceed_assets():
    """HTML のキャッシュが資産より長いと ValueError"""
    with pytest.raises(ValueError, match="以下にする"):
        _cfg(cache_seconds=60, html_cache_seconds=3600)


def test_invalid_inputs():
    """ホスト名とキャッシュ秒数の不正は ValueError"""
    with pytest.raises(ValueError):
        _cfg2("Example Storage")
    with pytest.raises(ValueError):
        _cfg(custom_domain="www_example_com")
    with pytest.raises(ValueError):
        _cfg(cache_seconds=-1)


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = _cfg()
    assert a == _cfg()
    assert json.loads(json.dumps(a)) == a
