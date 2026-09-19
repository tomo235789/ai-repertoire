"""カード database-encrypted-instance の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("database-encrypted-instance.py")
    spec = importlib.util.spec_from_file_location("database_encrypted_instance", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


encrypted_instance_config = _load().encrypted_instance_config

NETWORK = "projects/my-project/global/networks/example-vpc"
KEY = "projects/my-project/locations/asia-northeast1/keyRings/app-ring/cryptoKeys/data-key"


def _cfg(**kw):
    kwargs = {"private_network": NETWORK, "project_id": "my-project"}
    kwargs.update(kw)
    return encrypted_instance_config("example-db", "asia-northeast1", **kwargs)


def test_connection_name_length_limited():
    """<プロジェクト>:<インスタンス> は 98 文字まで"""
    with pytest.raises(ValueError, match="98 文字"):
        encrypted_instance_config(
            "a" * 90, "asia-northeast1",
            project_id="my-project", private_network=NETWORK,
        )


def test_private_ip_only_by_default():
    """限定公開 IP だけなら公開 IP は無効"""
    ip = _cfg()["settings"]["ipConfiguration"]
    assert ip["ipv4Enabled"] is False
    assert ip["privateNetwork"] == NETWORK
    assert ip["authorizedNetworks"] == []


def test_tls_required():
    """接続は TLS 必須。非推奨の requireSsl は併用できないので出さない"""
    ip = _cfg()["settings"]["ipConfiguration"]
    assert ip["sslMode"] == "ENCRYPTED_ONLY"
    assert "requireSsl" not in ip


def test_iam_authentication_flag_depends_on_engine():
    """IAM 認証のフラグ名は PostgreSQL と MySQL で違う"""
    assert _cfg()["settings"]["databaseFlags"] == [
        {"name": "cloudsql.iam_authentication", "value": "on"}
    ]
    assert _cfg(database_version="MYSQL_8_0")["settings"]["databaseFlags"] == [
        {"name": "cloudsql_iam_authentication", "value": "on"}
    ]
    with pytest.raises(ValueError, match="IAM 認証"):
        _cfg(database_version="SQLSERVER_2022_STANDARD")


def test_google_managed_key_by_default():
    """鍵を渡さなければ暗号化の設定キーは入らない"""
    assert "diskEncryptionConfiguration" not in _cfg()
    assert _cfg(kms_key_name=KEY)["diskEncryptionConfiguration"] == {"kmsKeyName": KEY}


def test_authorized_networks_sorted_and_enable_public_ip():
    """許可 CIDR を渡すと公開 IP が有効になり、CIDR 順に並ぶ"""
    ip = encrypted_instance_config(
        "example-db", "asia-northeast1", project_id="my-project",
        authorized_networks=["192.168.0.0/16", "10.0.0.0/8", "10.0.0.0/8"],
    )["settings"]["ipConfiguration"]
    assert ip["ipv4Enabled"] is True
    assert [n["value"] for n in ip["authorizedNetworks"]] == ["10.0.0.0/8", "192.168.0.0/16"]


def test_open_authorized_network_rejected():
    """公開 IP を全世界に開けない"""
    with pytest.raises(ValueError, match="全世界"):
        encrypted_instance_config(
            "example-db", "asia-northeast1",
            project_id="my-project", authorized_networks=["0.0.0.0/0"],
        )


def test_ipv6_authorized_network_rejected():
    """Cloud SQL の許可ネットワークは IPv4 だけ"""
    for cidr in ("::/0", "2001:db8::/32"):
        with pytest.raises(ValueError, match="IPv4"):
            encrypted_instance_config(
                "example-db", "asia-northeast1",
                project_id="my-project", authorized_networks=[cidr],
            )
    with pytest.raises(ValueError, match="CIDR"):
        encrypted_instance_config(
            "example-db", "asia-northeast1",
            project_id="my-project", authorized_networks=["10.0.0.1/8"],
        )


def test_connectivity_required():
    """限定公開 IP も許可ネットワークも無いと ValueError"""
    with pytest.raises(ValueError, match="誰も接続できない"):
        encrypted_instance_config(
            "example-db", "asia-northeast1", project_id="my-project"
        )


def test_deletion_protection_cannot_be_disabled():
    """削除保護は切れない"""
    with pytest.raises(ValueError, match="削除保護"):
        _cfg(deletion_protection=False)
    assert _cfg()["settings"]["deletionProtectionEnabled"] is True


def test_invalid_inputs():
    """名前・版・ディスク・可用性の不正は ValueError"""
    with pytest.raises(ValueError):
        encrypted_instance_config(
            "Example_DB", "asia-northeast1",
            project_id="my-project", private_network=NETWORK,
        )
    with pytest.raises(ValueError):
        _cfg(database_version="postgres16")
    with pytest.raises(ValueError):
        _cfg(disk_size_gb=9)
    with pytest.raises(ValueError):
        _cfg(availability_type="MULTI")


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = _cfg()
    assert a == _cfg()
    assert json.loads(json.dumps(a)) == a
