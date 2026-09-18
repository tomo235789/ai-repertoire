"""カード secret-fetch-at-runtime の Contract を検証するテスト"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("secret-fetch-at-runtime.py")
    spec = importlib.util.spec_from_file_location("secret_fetch_at_runtime", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load()
secret_version_name = _mod.secret_version_name
runtime_secret_config = _mod.runtime_secret_config

SA = "app-runner@my-project.iam.gserviceaccount.com"


def _cfg(**kw):
    return runtime_secret_config("my-project", {"DB_PASSWORD": "db-password"}, SA, **kw)


def test_version_name_format():
    """バージョンの完全名は projects/.../secrets/.../versions/... の形"""
    assert secret_version_name("my-project", "db-password") == (
        "projects/my-project/secrets/db-password/versions/latest"
    )
    assert secret_version_name("my-project", "db-password", "3").endswith("/versions/3")


def test_version_name_validation():
    """プロジェクト・シークレット名・バージョンの形式違いは ValueError"""
    with pytest.raises(ValueError):
        secret_version_name("My-Project", "db-password")
    with pytest.raises(ValueError):
        secret_version_name("my-project", "db password")
    with pytest.raises(ValueError):
        secret_version_name("my-project", "db-password", "v1")
    with pytest.raises(ValueError):
        secret_version_name("my-project", "db-password", "0")


def test_env_uses_secret_key_ref():
    """環境変数には参照だけが入り、値は入らない"""
    env = _cfg()["env"]
    assert env == [
        {
            "name": "DB_PASSWORD",
            "value_source": {"secret_key_ref": {"secret": "db-password", "version": "latest"}},
        }
    ]


def test_env_sorted():
    """環境変数は名前順に並ぶ"""
    cfg = runtime_secret_config("my-project", {"B_TOKEN": "b", "A_KEY": "a"}, SA)
    assert [e["name"] for e in cfg["env"]] == ["A_KEY", "B_TOKEN"]


def test_iam_binding_per_secret():
    """シークレットごとに accessor ロールのバインディングを作る"""
    binding = _cfg()["iam_bindings"][0]
    assert binding["resource"] == "projects/my-project/secrets/db-password"
    assert binding["role"] == "roles/secretmanager.secretAccessor"
    assert binding["members"] == [f"serviceAccount:{SA}"]


def test_pin_versions():
    """固定したバージョンが参照に入る"""
    env = _cfg(pin_versions={"DB_PASSWORD": "3"})["env"]
    assert env[0]["value_source"]["secret_key_ref"]["version"] == "3"
    with pytest.raises(ValueError, match="secrets に無い"):
        _cfg(pin_versions={"OTHER": "3"})


def test_invalid_inputs():
    """空の secrets、環境変数名、サービスアカウントの不正は ValueError"""
    with pytest.raises(ValueError):
        runtime_secret_config("my-project", {}, SA)
    with pytest.raises(ValueError):
        runtime_secret_config("my-project", {"db_password": "db-password"}, SA)
    with pytest.raises(ValueError):
        runtime_secret_config("my-project", {"DB_PASSWORD": "db-password"}, "app-runner")


def test_service_account_must_be_gserviceaccount():
    """人のメールアドレスはサービスアカウントとして受け付けない"""
    with pytest.raises(ValueError, match="gserviceaccount"):
        runtime_secret_config("my-project", {"A": "a"}, "user@example.com")


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    secrets = {"DB_PASSWORD": "db-password"}
    before = copy.deepcopy(secrets)
    cfg = runtime_secret_config("my-project", secrets, SA)
    assert secrets == before
    assert json.loads(json.dumps(cfg)) == cfg
