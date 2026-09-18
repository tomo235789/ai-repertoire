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


_mod = _load()
minimal_firewall_rules = _mod.minimal_firewall_rules
IAP_SOURCE_RANGE = _mod.IAP_SOURCE_RANGE


def _rules(allowed, **kw):
    return minimal_firewall_rules("example-vpc", "app", allowed, **kw)


def test_last_rule_denies_everything():
    """最後は優先度 65000 の全拒否"""
    last = _rules([("10.0.0.0/8", 443)])[-1]
    assert last["priority"] == 65000
    assert last["denied"] == [{"IPProtocol": "all"}]
    assert last["sourceRanges"] == ["0.0.0.0/0"]


def test_ports_grouped_by_source():
    """同じ送信元のポートは 1 本の規則にまとまる"""
    rules = _rules([("10.0.0.0/8", 443), ("10.0.0.0/8", 80)])
    assert len(rules) == 2  # 許可 1 本 + 全拒否
    assert rules[0]["allowed"][0]["ports"] == ["80", "443"]


def test_sources_sorted():
    """送信元ごとの規則は CIDR 順に並ぶ"""
    rules = _rules([("192.168.0.0/16", 443), ("10.0.0.0/8", 443)])
    assert [r["sourceRanges"][0] for r in rules[:2]] == ["10.0.0.0/8", "192.168.0.0/16"]


def test_target_tag_and_logging():
    """規則はタグで絞り、ログを有効にする"""
    for rule in _rules([("10.0.0.0/8", 443)]):
        assert rule["targetTags"] == ["app"]
        assert rule["logConfig"] == {"enable": True}
        assert rule["direction"] == "INGRESS"


def test_ssh_from_anywhere_rejected():
    """SSH と RDP を 0.0.0.0/0 に開けない"""
    with pytest.raises(ValueError, match="管理用ポート"):
        _rules([("0.0.0.0/0", 22)])
    with pytest.raises(ValueError, match="管理用ポート"):
        _rules([("0.0.0.0/0", 3389)])
    # Identity-Aware Proxy のレンジからは許す
    rules = _rules([(IAP_SOURCE_RANGE, 22)])
    assert rules[0]["allowed"][0]["ports"] == ["22"]


def test_https_from_anywhere_allowed():
    """HTTPS の全世界公開は許す"""
    assert _rules([("0.0.0.0/0", 443)])[0]["allowed"][0]["ports"] == ["443"]


def test_tag_length_limited_by_rule_name():
    """規則名が 63 文字を超えるタグは弾く"""
    with pytest.raises(ValueError, match="63 文字"):
        minimal_firewall_rules("example-vpc", "a" * 56, [("10.0.0.0/8", 443)])
    rules = minimal_firewall_rules("example-vpc", "a" * 54, [("10.0.0.0/8", 443)])
    assert all(len(rule["name"]) <= 63 for rule in rules)


def test_invalid_inputs():
    """タグ・許可リスト・ポート・CIDR・プロトコルの不正は ValueError"""
    with pytest.raises(ValueError):
        minimal_firewall_rules("example-vpc", "App", [("10.0.0.0/8", 443)])
    with pytest.raises(ValueError):
        _rules([])
    with pytest.raises(ValueError):
        _rules([("10.0.0.0/8", 0)])
    with pytest.raises(ValueError):
        _rules([("10.0.0.1/8", 443)])
    with pytest.raises(ValueError):
        _rules([("10.0.0.0/8", 443)], protocol="TCP")


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = _rules([("10.0.0.0/8", 443)])
    assert a == _rules([("10.0.0.0/8", 443)])
    assert json.loads(json.dumps(a)) == a
