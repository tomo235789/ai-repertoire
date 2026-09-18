"""カード storage-object-versioning の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path


def _load():
    path = Path(__file__).with_name("storage-object-versioning.py")
    spec = importlib.util.spec_from_file_location("storage_object_versioning", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


versioning_config = _load().versioning_config


def test_default_is_enabled_without_mfa():
    """既定は Enabled のみ。MFADelete キーは付かない"""
    cfg = versioning_config()
    assert cfg == {"Status": "Enabled"}
    json.dumps(cfg)


def test_disabled_means_suspended():
    """enabled=False は "Suspended"。"Disabled" は決して出力しない"""
    assert versioning_config(enabled=False) == {"Status": "Suspended"}


def test_mfa_delete_adds_key():
    """mfa_delete=True で MFADelete: Enabled が付く"""
    assert versioning_config(mfa_delete=True) == {"Status": "Enabled", "MFADelete": "Enabled"}
    assert versioning_config(enabled=False, mfa_delete=True) == {"Status": "Suspended", "MFADelete": "Enabled"}


def test_deterministic():
    """同じ入力に同じ出力"""
    assert versioning_config(True, True) == versioning_config(True, True)
