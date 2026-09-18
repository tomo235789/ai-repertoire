"""カード secret-kms-key の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("secret-kms-key.py")
    spec = importlib.util.spec_from_file_location("secret_kms_key", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load()
customer_managed_key = _mod.customer_managed_key
WRAP_KEY_OPS = _mod.WRAP_KEY_OPS

TENANT = "00000000-0000-0000-0000-000000000000"


def _cfg(**kw):
    return customer_managed_key("example-kv", "data-key", "japaneast", tenant_id=TENANT, **kw)


def test_vault_hardening():
    """RBAC・論理削除・消去保護・公衆ネットワーク遮断が既定"""
    props = _cfg()["vault"]["properties"]
    assert props["enableRbacAuthorization"] is True
    assert props["enableSoftDelete"] is True
    assert props["enablePurgeProtection"] is True
    assert props["publicNetworkAccess"] == "Disabled"
    assert props["networkAcls"]["defaultAction"] == "Deny"


def test_hsm_selects_premium_sku():
    """HSM 鍵は premium、ソフトウェア鍵は standard"""
    assert _cfg()["vault"]["properties"]["sku"]["name"] == "premium"
    assert _cfg(key_type="RSA")["vault"]["properties"]["sku"]["name"] == "standard"


def test_key_ops_limited_to_wrapping():
    """鍵の用途は暗号化・復号とラップ解除だけ。署名やエクスポートは許さない"""
    key = _cfg()["key"]["properties"]
    assert key["keyOps"] == list(WRAP_KEY_OPS)
    assert "sign" not in key["keyOps"]
    assert key["attributes"]["exportable"] is False


def test_rotation_triggers_from_creation():
    """ローテーションは作成からの経過で回す。期限からの逆算では最初の版が回らない"""
    policy = _cfg(rotation_period_days=365, expiry_days=730)["rotation_policy"]
    actions = {a["action"]["type"]: a["trigger"] for a in policy["lifetimeActions"]}
    assert actions["Rotate"] == {"timeAfterCreate": "P365D"}
    assert actions["Notify"] == {"timeBeforeExpiry": "P30D"}
    assert policy["attributes"]["expiryTime"] == "P730D"


def test_rotation_and_expiry_minimums():
    """ローテーションは 7 日以上、有効期間は 28 日以上"""
    with pytest.raises(ValueError, match="ローテーション間隔"):
        _cfg(rotation_period_days=6, expiry_days=730)
    with pytest.raises(ValueError, match="有効期間は"):
        _cfg(rotation_period_days=7, expiry_days=27)


def test_expiry_must_exceed_rotation():
    """有効期間がローテーション間隔以下だと ValueError"""
    with pytest.raises(ValueError, match="長くする"):
        _cfg(rotation_period_days=365, expiry_days=365)


def test_purge_protection_cannot_be_disabled():
    """消去保護は切れない"""
    with pytest.raises(ValueError, match="消去保護"):
        _cfg(purge_protection=False)


def test_invalid_inputs():
    """名前・鍵種別・鍵長・保持日数の不正は ValueError"""
    with pytest.raises(ValueError):
        customer_managed_key("Example_KV", "data-key", "japaneast", tenant_id=TENANT)
    with pytest.raises(ValueError):
        _cfg(key_type="EC")
    with pytest.raises(ValueError):
        _cfg(key_size=2048)
    with pytest.raises(ValueError):
        _cfg(soft_delete_retention_days=1)


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    assert _cfg() == _cfg()
    cfg = _cfg()
    assert json.loads(json.dumps(cfg)) == cfg
