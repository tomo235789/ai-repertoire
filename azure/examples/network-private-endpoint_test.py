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
PRIVATE_DNS_ZONES = _mod.PRIVATE_DNS_ZONES

SUBNET = (
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
    "/providers/Microsoft.Network/virtualNetworks/example-vnet/subnets/app"
)
TARGET = (
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
    "/providers/Microsoft.Storage/storageAccounts/examplestorage"
)


def test_auto_approved_connection():
    """既定は自動承認。手動承認用のキーは使わない"""
    cfg = private_endpoint_config("pe-blob", SUBNET, TARGET, "blob")
    props = cfg["endpoint"]["properties"]
    assert "privateLinkServiceConnections" in props
    assert "manualPrivateLinkServiceConnections" not in props
    conn = props["privateLinkServiceConnections"][0]
    assert conn["properties"] == {
        "privateLinkServiceId": TARGET,
        "groupIds": ["blob"],
    }


def test_manual_approval_uses_other_key():
    """手動承認では別のキーに入り、依頼文を添えられる"""
    cfg = private_endpoint_config(
        "pe-blob", SUBNET, TARGET, "blob", manual_approval=True, request_message="社内分析用"
    )
    props = cfg["endpoint"]["properties"]
    conn = props["manualPrivateLinkServiceConnections"][0]
    assert conn["properties"]["requestMessage"] == "社内分析用"
    assert "privateLinkServiceConnections" not in props


def test_dns_zone_matches_group_id():
    """サブリソースごとに対応するプライベート DNS ゾーンを返す"""
    assert private_endpoint_config("pe", SUBNET, TARGET, "blob")["private_dns_zone"] == (
        "privatelink.blob.core.windows.net"
    )
    assert private_endpoint_config("pe", SUBNET, TARGET, "vault")["private_dns_zone"] == (
        "privatelink.vaultcore.azure.net"
    )
    assert set(PRIVATE_DNS_ZONES) >= {"blob", "sqlServer", "vault", "registry"}


def test_dns_zone_group_is_opt_in():
    """ゾーン ID を渡したときだけゾーングループを作る"""
    assert private_endpoint_config("pe", SUBNET, TARGET, "blob")["dns_zone_group"] is None
    zone_id = (
        "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
        "/providers/Microsoft.Network/privateDnsZones/privatelink.blob.core.windows.net"
    )
    group = private_endpoint_config(
        "pe", SUBNET, TARGET, "blob", private_dns_zone_id=zone_id
    )["dns_zone_group"]
    assert group["properties"]["privateDnsZoneConfigs"] == [
        {
            "name": "privatelink-blob-core-windows-net",
            "properties": {"privateDnsZoneId": zone_id},
        }
    ]


def test_nic_name_derived_from_endpoint_name():
    """NIC 名はエンドポイント名から決まる"""
    cfg = private_endpoint_config("pe-blob", SUBNET, TARGET, "blob")
    assert cfg["endpoint"]["properties"]["customNetworkInterfaceName"] == "pe-blob-nic"


def test_request_message_requires_manual_approval():
    """自動承認で依頼文を渡すと ValueError"""
    with pytest.raises(ValueError, match="manual_approval"):
        private_endpoint_config("pe", SUBNET, TARGET, "blob", request_message="お願い")


def test_invalid_inputs():
    """空の名前、ARM ID でない値、未知のサブリソースは ValueError"""
    with pytest.raises(ValueError):
        private_endpoint_config("", SUBNET, TARGET, "blob")
    with pytest.raises(ValueError):
        private_endpoint_config("pe", "app", TARGET, "blob")
    with pytest.raises(ValueError):
        private_endpoint_config("pe", SUBNET, TARGET, "bucket")


def test_dns_zone_id_must_be_private_dns_zone():
    """DNS ゾーンは Microsoft.Network/privateDnsZones のリソース ID"""
    wrong = (
        "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
        "/providers/Microsoft.Network/virtualNetworks/example-vnet"
    )
    with pytest.raises(ValueError, match="privateDnsZones"):
        private_endpoint_config("pe", SUBNET, TARGET, "blob", private_dns_zone_id=wrong)


def test_subnet_id_must_be_a_subnet():
    """サブネットは virtualNetworks/<vnet>/subnets/<name> の形"""
    vnet_only = SUBNET.rsplit("/subnets/", 1)[0]
    with pytest.raises(ValueError, match="subnet_id"):
        private_endpoint_config("pe", vnet_only, TARGET, "blob")


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = private_endpoint_config("pe", SUBNET, TARGET, "blob")
    assert a == private_endpoint_config("pe", SUBNET, TARGET, "blob")
    assert json.loads(json.dumps(a)) == a
