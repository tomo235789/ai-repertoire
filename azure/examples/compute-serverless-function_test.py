"""カード compute-serverless-function の Contract を検証するテスト"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("compute-serverless-function.py")
    spec = importlib.util.spec_from_file_location("compute_serverless_function", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


serverless_function_config = _load().serverless_function_config

FARM = (
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
    "/providers/Microsoft.Web/serverfarms/example-plan"
)


def _cfg(**kw):
    return serverless_function_config("example-fn", "python3.12", "examplestorage", FARM, **kw)


def _settings(cfg):
    return {s["name"]: s["value"] for s in cfg["properties"]["siteConfig"]["appSettings"]}


def test_storage_uses_managed_identity():
    """ストレージ接続は接続文字列ではなくマネージド ID"""
    settings = _settings(_cfg())
    assert settings["AzureWebJobsStorage__accountName"] == "examplestorage"
    assert settings["AzureWebJobsStorage__credential"] == "managedidentity"
    assert "AzureWebJobsStorage" not in settings
    assert _cfg()["identity"] == {"type": "SystemAssigned"}


def test_transport_hardening():
    """HTTPS のみ、TLS 1.2 以上、FTPS は無効"""
    props = _cfg()["properties"]
    assert props["httpsOnly"] is True
    assert props["siteConfig"]["minTlsVersion"] == "1.2"
    assert props["siteConfig"]["ftpsState"] == "Disabled"


def test_runtime_mapping():
    """ランタイム名から linuxFxVersion とワーカー名が決まる"""
    cfg = serverless_function_config("example-fn", "node20", "examplestorage", FARM)
    assert cfg["properties"]["siteConfig"]["linuxFxVersion"] == "Node|20"
    assert _settings(cfg)["FUNCTIONS_WORKER_RUNTIME"] == "node"


def test_always_on_is_opt_in():
    """常時起動は明示したときだけ"""
    assert _cfg()["properties"]["siteConfig"]["alwaysOn"] is False
    assert _cfg(always_on=True)["properties"]["siteConfig"]["alwaysOn"] is True


def test_app_settings_sorted_and_merged():
    """追加設定は既定と混ぜて名前順に並ぶ"""
    names = [s["name"] for s in _cfg(app_settings={"MY_FLAG": "on"})["properties"]["siteConfig"]["appSettings"]]
    assert names == sorted(names)
    assert "MY_FLAG" in names


def test_reserved_setting_cannot_be_overridden():
    """予約済みの設定は上書きできない"""
    with pytest.raises(ValueError, match="予約済み"):
        _cfg(app_settings={"FUNCTIONS_WORKER_RUNTIME": "node"})


def test_plaintext_secret_rejected():
    """接続文字列らしい平文はアプリ設定に入れられない"""
    with pytest.raises(ValueError, match="秘密値"):
        _cfg(app_settings={"DB": "AccountName=a;AccountKey=abc=="})


def test_invalid_inputs():
    """名前とランタイムの不正は ValueError"""
    with pytest.raises(ValueError):
        serverless_function_config("Example_FN", "python3.12", "examplestorage", FARM)
    with pytest.raises(ValueError):
        serverless_function_config("example-fn", "ruby3.3", "examplestorage", FARM)


def test_secret_named_settings_require_key_vault_reference():
    """秘密用途の名前には Key Vault 参照だけを許す"""
    for key in ("DB_PASSWORD", "API_TOKEN", "MY_CLIENT_SECRET", "STORAGE_ACCESS_KEY"):
        with pytest.raises(ValueError, match="秘密値"):
            _cfg(app_settings={key: "hunter2"})
    cfg = _cfg(
        app_settings={"DB_PASSWORD": "@Microsoft.KeyVault(SecretUri=https://kv.vault.azure.net/secrets/db)"}
    )
    assert any(s["name"] == "DB_PASSWORD" for s in cfg["properties"]["siteConfig"]["appSettings"])


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    extra = {"MY_FLAG": "on"}
    before = copy.deepcopy(extra)
    cfg = _cfg(app_settings=extra)
    assert extra == before
    assert json.loads(json.dumps(cfg)) == cfg
