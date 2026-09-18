"""カード network-private-subnet の Contract を検証するテスト"""

import copy
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


def _cfg(**kw):
    return private_subnet_config("app", "example-vpc", "10.0.1.0/24", "asia-northeast1", **kw)


def test_private_google_access_enabled():
    """外部 IP なしで Google API に出られるようにする"""
    assert _cfg()["subnetwork"]["privateIpGoogleAccess"] is True


def test_flow_logs_enabled():
    """フローログは既定で有効。サンプリング率は引数で決まる"""
    log = _cfg()["subnetwork"]["logConfig"]
    assert log["enable"] is True
    assert log["flowSampling"] == 0.5
    assert _cfg(flow_log_sampling=1.0)["subnetwork"]["logConfig"]["flowSampling"] == 1.0


def test_usable_addresses_excludes_reserved():
    """GCP が予約する 4 アドレスを引いた数を返す"""
    assert _cfg()["usable_addresses"] == 252
    assert private_subnet_config(
        "app", "example-vpc", "10.0.1.0/29", "asia-northeast1"
    )["usable_addresses"] == 4


def test_secondary_ranges_sorted():
    """副レンジは名前順に並ぶ"""
    cfg = _cfg(secondary_ranges={"services": "10.2.0.0/20", "pods": "10.1.0.0/16"})
    assert [r["rangeName"] for r in cfg["subnetwork"]["secondaryIpRanges"]] == [
        "pods",
        "services",
    ]


def test_no_secondary_key_when_empty():
    """副レンジが無ければキー自体を作らない"""
    assert "secondaryIpRanges" not in _cfg()["subnetwork"]


def test_overlapping_secondary_rejected():
    """副レンジが主レンジと重なると ValueError"""
    with pytest.raises(ValueError, match="重なる"):
        _cfg(secondary_ranges={"pods": "10.0.1.0/28"})


def test_overlapping_secondaries_rejected():
    """副レンジ同士が重なると ValueError"""
    with pytest.raises(ValueError, match="副レンジ同士"):
        _cfg(secondary_ranges={"pods": "10.1.0.0/16", "services": "10.1.1.0/24"})


def test_purpose_limited_to_private():
    """ワークロード用のサブネットだけを作る"""
    with pytest.raises(ValueError, match="purpose=PRIVATE"):
        _cfg(purpose="REGIONAL_MANAGED_PROXY")


def test_prefix_length_range():
    """主レンジも副レンジも /4〜/29"""
    with pytest.raises(ValueError, match="/4〜/29"):
        private_subnet_config("app", "example-vpc", "0.0.0.0/3", "asia-northeast1")
    with pytest.raises(ValueError, match="副レンジは /4〜/29"):
        _cfg(secondary_ranges={"pods": "10.1.0.0/30"})


def test_invalid_inputs():
    """名前・CIDR・プレフィックス長・サンプリング率の不正は ValueError"""
    with pytest.raises(ValueError):
        private_subnet_config("App", "example-vpc", "10.0.1.0/24", "asia-northeast1")
    with pytest.raises(ValueError):
        private_subnet_config("app", "example-vpc", "10.0.1.5/24", "asia-northeast1")
    with pytest.raises(ValueError):
        private_subnet_config("app", "example-vpc", "10.0.1.0/30", "asia-northeast1")
    with pytest.raises(ValueError):
        _cfg(flow_log_sampling=0)
    with pytest.raises(ValueError):
        _cfg(flow_log_sampling=1.5)


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    ranges = {"pods": "10.1.0.0/16"}
    before = copy.deepcopy(ranges)
    cfg = _cfg(secondary_ranges=ranges)
    assert ranges == before
    assert json.loads(json.dumps(cfg)) == cfg
