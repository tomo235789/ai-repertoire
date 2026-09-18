"""カード network-security-group-minimal の Contract を検証するテスト"""

import importlib
import json

import pytest

mod = importlib.import_module("network-security-group-minimal")
minimal_security_group = mod.minimal_security_group
Rule = mod.Rule


def test_snapshot():
    """出力の形（boto3 kwargs）"""
    out = minimal_security_group(
        "app",
        "vpc-0abc",
        [
            Rule(443, "from ALB", source_sg="sg-0alb"),
            Rule(8080, "from office", cidr="10.0.0.0/8"),
        ],
    )
    assert out == {
        "create_security_group": {"GroupName": "app", "Description": "app", "VpcId": "vpc-0abc"},
        "authorize_ingress": [
            {
                "IpProtocol": "tcp",
                "FromPort": 443,
                "ToPort": 443,
                "UserIdGroupPairs": [{"GroupId": "sg-0alb", "Description": "from ALB"}],
            },
            {
                "IpProtocol": "tcp",
                "FromPort": 8080,
                "ToPort": 8080,
                "IpRanges": [{"CidrIp": "10.0.0.0/8", "Description": "from office"}],
            },
        ],
        "authorize_egress": [],
        "revoke_egress": [{"IpProtocol": "-1", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}],
    }
    json.dumps(out)


def test_egress_default_is_deny_and_egress_all_opt_in():
    """既定は egress 無し（既定の全許可を取り消す）。egress_all=True で全許可を 1 つ足す"""
    closed = minimal_security_group("app", "vpc-0abc", [])
    assert closed["authorize_egress"] == []
    assert closed["revoke_egress"] == [{"IpProtocol": "-1", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]
    opened = minimal_security_group("app", "vpc-0abc", [], egress_all=True)
    assert opened["authorize_egress"] == [{"IpProtocol": "-1", "IpRanges": [{"CidrIp": "0.0.0.0/0"}]}]
    assert opened["revoke_egress"] == []


@pytest.mark.parametrize(
    "rule",
    [
        Rule(22, "ssh", cidr="0.0.0.0/0"),
        Rule(3389, "rdp", cidr="0.0.0.0/0"),
        Rule(22, "ssh", cidr="::/0"),
        Rule(20, "range incl 22", cidr="0.0.0.0/0", to_port=25),
        Rule(0, "all ports", cidr="0.0.0.0/0", to_port=65535),
    ],
)
def test_admin_ports_from_anywhere_rejected(rule):
    """0.0.0.0/0 や ::/0 から 22 / 3389 を含む範囲は ValueError"""
    with pytest.raises(ValueError):
        minimal_security_group("app", "vpc-0abc", [rule])


def test_admin_ports_from_private_cidr_allowed():
    """22 でも送信元が限定されていれば許可する"""
    out = minimal_security_group("bastion", "vpc-0abc", [Rule(22, "ssh from office", cidr="203.0.113.0/24")])
    assert out["authorize_ingress"][0]["IpRanges"] == [{"CidrIp": "203.0.113.0/24", "Description": "ssh from office"}]


def test_ipv6_cidr_goes_to_ipv6ranges():
    """IPv6 の CIDR は Ipv6Ranges に入る"""
    out = minimal_security_group("app", "vpc-0abc", [Rule(443, "v6", cidr="2001:db8::/32")])
    perm = out["authorize_ingress"][0]
    assert perm["Ipv6Ranges"] == [{"CidrIpv6": "2001:db8::/32", "Description": "v6"}]
    assert "IpRanges" not in perm


@pytest.mark.parametrize(
    "rule",
    [
        Rule(443, "", cidr="10.0.0.0/8"),
        Rule(443, "   ", cidr="10.0.0.0/8"),
        Rule(443, "both", cidr="10.0.0.0/8", source_sg="sg-0abc"),
        Rule(443, "neither"),
        Rule(443, "bad cidr", cidr="10.0.0.1/8"),
        Rule(443, "bad sg", source_sg="vpc-0abc"),
        Rule(443, "all proto", cidr="10.0.0.0/8", protocol="-1"),
        Rule(70000, "port", cidr="10.0.0.0/8"),
        Rule(443, "range", cidr="10.0.0.0/8", to_port=80),
    ],
)
def test_invalid_rule_rejected(rule):
    """description 無し・cidr と source_sg の両方/どちらも無し・不正 CIDR・全プロトコル・不正ポートは ValueError"""
    with pytest.raises(ValueError):
        minimal_security_group("app", "vpc-0abc", [rule])


def test_invalid_group_args_rejected():
    """name 空・vpc_id 形式違いは ValueError"""
    with pytest.raises(ValueError):
        minimal_security_group("", "vpc-0abc", [])
    with pytest.raises(ValueError):
        minimal_security_group("app", "sg-0abc", [])


def test_is_deterministic_and_input_untouched():
    """同じ入力から同じ出力。Rule は frozen で変更されない"""
    rules = [Rule(443, "https", cidr="10.0.0.0/8")]
    a = minimal_security_group("app", "vpc-0abc", rules, description="app sg")
    b = minimal_security_group("app", "vpc-0abc", rules, description="app sg")
    assert a == b
    assert a["create_security_group"]["Description"] == "app sg"
    assert rules == [Rule(443, "https", cidr="10.0.0.0/8")]
