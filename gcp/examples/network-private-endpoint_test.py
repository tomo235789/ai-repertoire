"""カード network-private-endpoint の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("network-private-endpoint.py")
    spec = importlib.util.spec_from_file_location("network_private_endpoint", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load()
private_endpoint_config = _mod.private_endpoint_config
RECOMMENDED_ADDRESSES = _mod.RECOMMENDED_ADDRESSES

ATTACHMENT = "projects/other-project/regions/asia-northeast1/serviceAttachments/example-sa"
SUBNET = "projects/my-project/regions/asia-northeast1/subnetworks/app"


def test_api_bundle_endpoint_is_global():
    """Google API のバンドルはグローバル転送ルールになる"""
    cfg = private_endpoint_config("pscapis", "example-vpc", "10.0.0.100", api_bundle="all-apis")
    assert cfg["scope"] == "global"
    assert cfg["forwarding_rule"]["target"] == "all-apis"
    assert "subnetwork" not in cfg["forwarding_rule"]


def test_api_bundle_returns_dns_zone():
    """バンドルでは名前解決を差し替える DNS ゾーンも返る"""
    zone = private_endpoint_config(
        "pscapis", "example-vpc", "10.0.0.100", api_bundle="all-apis"
    )["dns_zone"]
    assert zone["dns_name"] == "p.googleapis.com."
    assert zone["visibility"] == "private"
    assert zone["records"][0]["rrdatas"] == ["10.0.0.100"]


def test_service_attachment_endpoint_is_regional():
    """個別サービスへのエンドポイントはリージョンで、サブネットが要る"""
    cfg = private_endpoint_config(
        "psc-db", "example-vpc", "10.0.1.50", target_service=ATTACHMENT, subnetwork=SUBNET
    )
    assert cfg["scope"] == "regional"
    assert cfg["forwarding_rule"]["subnetwork"] == SUBNET
    assert cfg["forwarding_rule"]["allowPscGlobalAccess"] is False
    assert cfg["dns_zone"] is None


def test_global_access_opt_in():
    """他リージョンからの接続は明示したときだけ"""
    cfg = private_endpoint_config(
        "psc-db", "example-vpc", "10.0.1.50",
        target_service=ATTACHMENT, subnetwork=SUBNET, allow_psc_global_access=True,
    )
    assert cfg["forwarding_rule"]["allowPscGlobalAccess"] is True


def test_target_is_exclusive():
    """バンドルと個別サービスは同時に指定できず、どちらも省略もできない"""
    with pytest.raises(ValueError, match="どちらか一方"):
        private_endpoint_config("psc", "example-vpc", "10.0.0.100")
    with pytest.raises(ValueError, match="どちらか一方"):
        private_endpoint_config(
            "psc", "example-vpc", "10.0.0.100", api_bundle="all-apis", target_service=ATTACHMENT
        )


def test_service_attachment_needs_subnetwork():
    """個別サービスにサブネットが無いと ValueError"""
    with pytest.raises(ValueError, match="サブネット"):
        private_endpoint_config("psc", "example-vpc", "10.0.1.50", target_service=ATTACHMENT)


def test_recommended_addresses_documented():
    """バンドルごとの推奨 IP レンジを参照できる"""
    assert RECOMMENDED_ADDRESSES["all-apis"] == "199.36.153.8/30"
    assert RECOMMENDED_ADDRESSES["vpc-sc"] == "199.36.153.4/30"


def test_bundle_name_is_restricted():
    """バンドル向けの転送ルール名はハイフンを含められず 20 文字まで"""
    with pytest.raises(ValueError, match="20 文字"):
        private_endpoint_config("psc-apis", "example-vpc", "10.0.0.100", api_bundle="all-apis")
    # 個別サービス向けにはハイフンを使える
    cfg = private_endpoint_config(
        "psc-db", "example-vpc", "10.0.1.50", target_service=ATTACHMENT, subnetwork=SUBNET
    )
    assert cfg["forwarding_rule"]["name"] == "psc-db"


def test_ipv6_rejected():
    """Private Service Connect は IPv4 のみ"""
    with pytest.raises(ValueError, match="IPv4"):
        private_endpoint_config("pscapis", "example-vpc", "2001:db8::1", api_bundle="all-apis")


def test_invalid_inputs():
    """名前・IP・バンドルの不正は ValueError"""
    with pytest.raises(ValueError):
        private_endpoint_config("PSC", "example-vpc", "10.0.0.100", api_bundle="all-apis")
    with pytest.raises(ValueError):
        private_endpoint_config("psc", "example-vpc", "10.0.0.300", api_bundle="all-apis")
    with pytest.raises(ValueError):
        private_endpoint_config("psc", "example-vpc", "10.0.0.100", api_bundle="some-apis")


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = private_endpoint_config("pscapis", "example-vpc", "10.0.0.100", api_bundle="all-apis")
    assert a == private_endpoint_config(
        "pscapis", "example-vpc", "10.0.0.100", api_bundle="all-apis"
    )
    assert json.loads(json.dumps(a)) == a
