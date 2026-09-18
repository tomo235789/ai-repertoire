"""カード network-private-subnet の Contract を検証するテスト"""

import importlib
import json

import pytest

mod = importlib.import_module("network-private-subnet")
private_subnet = mod.private_subnet

TAGS = {"Name": "app-private-a", "Env": "prod"}


def test_snapshot():
    """出力の形（boto3 kwargs）"""
    out = private_subnet("vpc-0abc", "10.0.1.0/24", "us-east-1a", TAGS, vpc_cidr="10.0.0.0/16")
    assert out == {
        "create_subnet": {
            "VpcId": "vpc-0abc",
            "CidrBlock": "10.0.1.0/24",
            "AvailabilityZone": "us-east-1a",
            "TagSpecifications": [
                {
                    "ResourceType": "subnet",
                    "Tags": [{"Key": "Name", "Value": "app-private-a"}, {"Key": "Env", "Value": "prod"}],
                }
            ],
        },
        "modify_subnet_attribute": {"MapPublicIpOnLaunch": {"Value": False}},
        "route_table": {
            "VpcId": "vpc-0abc",
            "TagSpecifications": [
                {
                    "ResourceType": "route-table",
                    "Tags": [{"Key": "Name", "Value": "app-private-a"}, {"Key": "Env", "Value": "prod"}],
                }
            ],
        },
    }
    json.dumps(out)


def test_no_public_ip_and_no_igw_route():
    """パブリック IP を付与せず、ルートテーブルに IGW への経路が無い"""
    out = private_subnet("vpc-0abc", "10.0.1.0/24", "us-east-1a", TAGS)
    assert out["modify_subnet_attribute"]["MapPublicIpOnLaunch"] == {"Value": False}
    assert "MapPublicIpOnLaunch" not in out["create_subnet"]
    assert "GatewayId" not in json.dumps(out)
    assert "0.0.0.0/0" not in json.dumps(out)


def test_is_deterministic_and_does_not_mutate_input():
    """同じ入力から同じ出力。引数の tags は変更しない"""
    tags = dict(TAGS)
    a = private_subnet("vpc-0abc", "10.0.1.0/24", "us-east-1a", tags)
    b = private_subnet("vpc-0abc", "10.0.1.0/24", "us-east-1a", tags)
    assert a == b
    assert tags == TAGS


@pytest.mark.parametrize(
    "cidr",
    ["10.0.1.5/24", "10.0.1.0", "10.0.0.0/8", "10.0.1.0/29", "2001:db8::/64", "not-a-cidr"],
)
def test_invalid_cidr_raises(cidr):
    """ホストビット付き・プレフィックス無し・/16〜/28 外・IPv6・不正文字列は ValueError"""
    with pytest.raises(ValueError):
        private_subnet("vpc-0abc", cidr, "us-east-1a", TAGS)


def test_cidr_outside_vpc_raises():
    """vpc_cidr を渡した場合、含まれない CIDR は ValueError"""
    with pytest.raises(ValueError):
        private_subnet("vpc-0abc", "192.168.1.0/24", "us-east-1a", TAGS, vpc_cidr="10.0.0.0/16")
    with pytest.raises(ValueError):
        private_subnet("vpc-0abc", "10.0.1.0/24", "us-east-1a", TAGS, vpc_cidr="bad")


def test_invalid_identifiers_raise():
    """vpc_id の形式違い・空の az・空の tags は ValueError"""
    with pytest.raises(ValueError):
        private_subnet("subnet-0abc", "10.0.1.0/24", "us-east-1a", TAGS)
    with pytest.raises(ValueError):
        private_subnet("vpc-0abc", "10.0.1.0/24", "", TAGS)
    with pytest.raises(ValueError):
        private_subnet("vpc-0abc", "10.0.1.0/24", "us-east-1a", {})
