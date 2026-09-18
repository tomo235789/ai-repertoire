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


customer_managed_key = _load().customer_managed_key

SA = "serviceAccount:app@my-project.iam.gserviceaccount.com"


NEXT_ROTATION = "2026-12-18T00:00:00Z"


def _cfg(**kw):
    kwargs = {"next_rotation_time": NEXT_ROTATION}
    kwargs.update(kw)
    return customer_managed_key(
        "my-project", "asia-northeast1", "app-ring", "data-key", **kwargs
    )


def test_resource_names():
    """キーリングと鍵の親子関係が名前に表れる"""
    cfg = _cfg()
    assert cfg["key_ring"]["parent"] == "projects/my-project/locations/asia-northeast1"
    assert cfg["crypto_key"]["parent"].endswith("/keyRings/app-ring")
    assert cfg["iam_binding"]["resource"].endswith("/cryptoKeys/data-key")


def test_durations_in_seconds():
    """ローテーションと破棄待ちは秒の文字列で渡す"""
    key = _cfg(rotation_period_days=90, destroy_scheduled_days=30)["crypto_key"]["crypto_key"]
    assert key["rotation_period"] == f"{90 * 86400}s"
    assert key["destroy_scheduled_duration"] == f"{30 * 86400}s"


def test_next_rotation_time_required():
    """間隔だけでは自動ローテーションが始まらないので次回時刻も入れる"""
    key = _cfg()["crypto_key"]["crypto_key"]
    assert key["next_rotation_time"] == NEXT_ROTATION
    with pytest.raises(ValueError, match="RFC 3339"):
        _cfg(next_rotation_time="2026-12-18")


def test_purpose_and_protection():
    """用途は暗号化・復号、既定の保護レベルは HSM"""
    key = _cfg()["crypto_key"]["crypto_key"]
    assert key["purpose"] == "ENCRYPT_DECRYPT"
    assert key["version_template"] == {
        "protection_level": "HSM",
        "algorithm": "GOOGLE_SYMMETRIC_ENCRYPTION",
    }
    assert _cfg(protection_level="SOFTWARE")["crypto_key"]["crypto_key"]["version_template"][
        "protection_level"
    ] == "SOFTWARE"


def test_iam_members_sorted_and_deduplicated():
    """鍵を使うメンバーは重複を除いて名前順"""
    binding = _cfg(encrypter_members=[SA, SA, "user:a@example.com"])["iam_binding"]
    assert binding["role"] == "roles/cloudkms.cryptoKeyEncrypterDecrypter"
    assert binding["members"] == sorted({SA, "user:a@example.com"})


def test_destroy_delay_minimum():
    """破棄待ちは 7 日以上"""
    with pytest.raises(ValueError, match="破棄待ち"):
        _cfg(destroy_scheduled_days=6)
    assert _cfg(destroy_scheduled_days=7)


def test_next_rotation_time_must_exist():
    """形だけ合っていても実在しない日時は弾く"""
    with pytest.raises(ValueError, match="実在しない"):
        _cfg(next_rotation_time="2026-99-99T99:99:99Z")


def test_destroy_and_rotation_upper_bounds():
    """破棄待ちは 120 日まで、ローテーション間隔にも上限がある"""
    with pytest.raises(ValueError, match="破棄待ち"):
        _cfg(destroy_scheduled_days=121)
    with pytest.raises(ValueError, match="ローテーション間隔"):
        _cfg(rotation_period_days=876_000 // 24 + 1)


def test_invalid_inputs():
    """名前・保護レベル・ローテーション・メンバーの不正は ValueError"""
    with pytest.raises(ValueError):
        customer_managed_key(
            "my-project", "asia-northeast1", "app ring", "data-key",
            next_rotation_time=NEXT_ROTATION,
        )
    with pytest.raises(ValueError):
        _cfg(protection_level="SOFT")
    with pytest.raises(ValueError):
        _cfg(rotation_period_days=0)
    with pytest.raises(ValueError):
        _cfg(encrypter_members=["app@my-project.iam.gserviceaccount.com"])


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = _cfg()
    assert a == _cfg()
    assert json.loads(json.dumps(a)) == a
