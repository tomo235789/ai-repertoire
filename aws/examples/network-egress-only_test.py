"""カード network-egress-only の Contract を検証するテスト"""

import importlib
import json

import pytest

mod = importlib.import_module("network-egress-only")
egress_only_route = mod.egress_only_route


def test_snapshot_dual_stack():
    """IPv4 は NAT、IPv6 は Egress-only IGW の 2 経路"""
    out = egress_only_route("rtb-0abc", nat_gateway_id="nat-0abc", egress_only_igw_id="eigw-0abc")
    assert out == [
        {"RouteTableId": "rtb-0abc", "DestinationCidrBlock": "0.0.0.0/0", "NatGatewayId": "nat-0abc"},
        {
            "RouteTableId": "rtb-0abc",
            "DestinationIpv6CidrBlock": "::/0",
            "EgressOnlyInternetGatewayId": "eigw-0abc",
        },
    ]
    json.dumps(out)


def test_ipv4_only_and_ipv6_only():
    """渡した ID の分だけ経路を作る"""
    v4 = egress_only_route("rtb-0abc", nat_gateway_id="nat-0abc")
    assert len(v4) == 1 and v4[0]["DestinationCidrBlock"] == "0.0.0.0/0"
    v6 = egress_only_route("rtb-0abc", egress_only_igw_id="eigw-0abc")
    assert len(v6) == 1 and v6[0]["DestinationIpv6CidrBlock"] == "::/0"


def test_never_creates_inbound_capable_route():
    """GatewayId（Internet Gateway）を含む経路は作らない"""
    out = egress_only_route("rtb-0abc", nat_gateway_id="nat-0abc", egress_only_igw_id="eigw-0abc")
    for route in out:
        assert "GatewayId" not in route
        assert set(route) <= {
            "RouteTableId",
            "DestinationCidrBlock",
            "DestinationIpv6CidrBlock",
            "NatGatewayId",
            "EgressOnlyInternetGatewayId",
        }


def test_both_none_raises():
    """両方 None は ValueError"""
    with pytest.raises(ValueError):
        egress_only_route("rtb-0abc")


def test_internet_gateway_id_rejected():
    """igw- を渡すと ValueError（入向きの経路になるため）"""
    with pytest.raises(ValueError):
        egress_only_route("rtb-0abc", nat_gateway_id="igw-0abc")
    with pytest.raises(ValueError):
        egress_only_route("rtb-0abc", egress_only_igw_id="igw-0abc")


def test_invalid_route_table_id_raises():
    """route_table_id の形式違いは ValueError"""
    with pytest.raises(ValueError):
        egress_only_route("subnet-0abc", nat_gateway_id="nat-0abc")


def test_is_deterministic():
    """同じ入力から同じ出力"""
    a = egress_only_route("rtb-0abc", nat_gateway_id="nat-0abc")
    b = egress_only_route("rtb-0abc", nat_gateway_id="nat-0abc")
    assert a == b
