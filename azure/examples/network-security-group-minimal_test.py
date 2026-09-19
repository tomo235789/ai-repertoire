"""カード network-security-group-minimal の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("network-security-group-minimal.py")
    spec = importlib.util.spec_from_file_location("network_security_group_minimal", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


minimal_inbound_rules = _load().minimal_inbound_rules


def test_last_rule_denies_everything():
    """最後は必ず全拒否。既定規則より前で落とす"""
    rules = minimal_inbound_rules([("10.0.0.0/8", 443)])
    last = rules[-1]
    assert last["name"] == "deny-all-inbound"
    assert last["properties"]["access"] == "Deny"
    assert last["properties"]["priority"] == 4000


def test_priorities_ascend():
    """優先度は 100 から 10 刻みで、重複しない"""
    rules = minimal_inbound_rules([("10.0.0.0/8", 443), ("10.0.0.0/8", 80)])
    priorities = [r["properties"]["priority"] for r in rules]
    assert priorities == [100, 110, 4000]


def test_duplicates_collapse():
    """同じ組を 2 度書いても規則は 1 本"""
    rules = minimal_inbound_rules([("10.0.0.0/8", 443), ("10.0.0.0/8", 443)])
    assert len(rules) == 2  # 許可 1 本 + 全拒否


def test_service_tag_allowed():
    """サービスタグは CIDR でなくてもそのまま通る"""
    rules = minimal_inbound_rules([("VirtualNetwork", 443)])
    assert rules[0]["properties"]["sourceAddressPrefix"] == "VirtualNetwork"


def test_management_port_from_internet_rejected():
    """SSH と RDP はインターネットに開けない"""
    for source in ("*", "Internet", "0.0.0.0/0", "::/0"):
        with pytest.raises(ValueError, match="管理用ポート"):
            minimal_inbound_rules([(source, 22)])
        with pytest.raises(ValueError, match="管理用ポート"):
            minimal_inbound_rules([(source, 3389)])
    # 社内からの SSH は許す
    rules = minimal_inbound_rules([("203.0.113.0/24", 22)])
    assert rules[0]["properties"]["destinationPortRange"] == "22"


def test_https_from_internet_allowed():
    """HTTPS の全世界公開は許す"""
    rules = minimal_inbound_rules([("Internet", 443)])
    assert rules[0]["properties"]["access"] == "Allow"


def test_invalid_inputs():
    """空の許可リスト、範囲外ポート、壊れた CIDR、規則の作りすぎは ValueError"""
    with pytest.raises(ValueError):
        minimal_inbound_rules([])
    with pytest.raises(ValueError):
        minimal_inbound_rules([("10.0.0.0/8", 0)])
    with pytest.raises(ValueError):
        minimal_inbound_rules([("10.0.0.256/8", 443)])
    with pytest.raises(ValueError):
        minimal_inbound_rules([("10.0.0.0/8", p) for p in range(1000, 1400)])
    with pytest.raises(ValueError):
        minimal_inbound_rules([("10.0.0.0/8", 443)], protocol="tcp")


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = minimal_inbound_rules([("10.0.0.0/8", 443)])
    assert a == minimal_inbound_rules([("10.0.0.0/8", 443)])
    assert json.loads(json.dumps(a)) == a
