"""カード network-private-subnet の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("network-private-subnet.py")
    spec = importlib.util.spec_from_file_location("network_private_subnet", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


private_subnet_config = _load().private_subnet_config


def test_no_default_outbound_access():
    """既定の送信インターネットアクセスには頼らない"""
    cfg = private_subnet_config("app", "10.0.1.0/24")
    assert cfg["properties"]["defaultOutboundAccess"] is False


def test_network_policies_stay_enabled():
    """プライベートエンドポイントにも NSG を効かせるためポリシーは有効のまま"""
    props = private_subnet_config("app", "10.0.1.0/24")["properties"]
    assert props["privateEndpointNetworkPolicies"] == "Enabled"
    assert props["privateLinkServiceNetworkPolicies"] == "Enabled"


def test_usable_addresses_excludes_reserved():
    """Azure が予約する 5 アドレスを引いた数を返す"""
    assert private_subnet_config("app", "10.0.1.0/24")["usable_addresses"] == 251
    assert private_subnet_config("app", "10.0.1.0/29")["usable_addresses"] == 3


def test_optional_attachments():
    """ルートテーブル・NAT・NSG は渡したときだけキーが入る"""
    cfg = private_subnet_config("app", "10.0.1.0/24")
    for key in ("routeTable", "natGateway", "networkSecurityGroup", "delegations"):
        assert key not in cfg["properties"]
    cfg = private_subnet_config(
        "app",
        "10.0.1.0/24",
        route_table_id="/subscriptions/s/rt",
        nat_gateway_id="/subscriptions/s/nat",
        network_security_group_id="/subscriptions/s/nsg",
    )
    assert cfg["properties"]["natGateway"] == {"id": "/subscriptions/s/nat"}


def test_service_endpoints_sorted():
    """サービスエンドポイントは名前順に並ぶ"""
    cfg = private_subnet_config(
        "app", "10.0.1.0/24", service_endpoints=["Microsoft.Sql", "Microsoft.Storage"]
    )
    assert cfg["properties"]["serviceEndpoints"] == [
        {"service": "Microsoft.Sql"},
        {"service": "Microsoft.Storage"},
    ]


def test_delegation():
    """委任先はサービス名から決まる名前で 1 件入る"""
    cfg = private_subnet_config(
        "app", "10.0.1.0/24", delegation_service="Microsoft.App/environments"
    )
    assert cfg["properties"]["delegations"] == [
        {
            "name": "microsoft.app-environments",
            "properties": {"serviceName": "Microsoft.App/environments"},
        }
    ]


def test_invalid_inputs():
    """名前・CIDR・プレフィックス長の不正は ValueError"""
    with pytest.raises(ValueError):
        private_subnet_config("-app", "10.0.1.0/24")
    with pytest.raises(ValueError):
        private_subnet_config("app", "10.0.1.5/24")  # ホスト部が残っている
    with pytest.raises(ValueError):
        private_subnet_config("app", "10.0.1.0/30")
    with pytest.raises(ValueError):
        private_subnet_config("app", "not-a-cidr")


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = private_subnet_config("app", "10.0.1.0/24")
    assert a == private_subnet_config("app", "10.0.1.0/24")
    assert json.loads(json.dumps(a)) == a
