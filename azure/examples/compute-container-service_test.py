"""カード compute-container-service の Contract を検証するテスト"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("compute-container-service.py")
    spec = importlib.util.spec_from_file_location("compute_container_service", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


container_service_config = _load().container_service_config

ENV_ID = (
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
    "/providers/Microsoft.App/managedEnvironments/example-env"
)
IMAGE = "example.azurecr.io/api:1.4.2"


def test_ingress_is_internal_by_default():
    """既定では環境の内部だけに公開し、平文 HTTP は許さない"""
    cfg = container_service_config("example-api", IMAGE, ENV_ID)
    ingress = cfg["properties"]["configuration"]["ingress"]
    assert ingress["external"] is False
    assert ingress["allowInsecure"] is False
    assert ingress["targetPort"] == 8080
    assert ingress["traffic"] == [{"latestRevision": True, "weight": 100}]


def test_external_ingress_opt_in():
    """インターネット公開は明示したときだけ"""
    cfg = container_service_config("example-api", IMAGE, ENV_ID, external_ingress=True)
    assert cfg["properties"]["configuration"]["ingress"]["external"] is True


def test_memory_follows_cpu():
    """メモリは CPU の 2 倍の GiB で決まる"""
    for cpu, memory in [(0.25, "0.5Gi"), (0.5, "1Gi"), (2.0, "4Gi")]:
        cfg = container_service_config("example-api", IMAGE, ENV_ID, cpu=cpu)
        res = cfg["properties"]["template"]["containers"][0]["resources"]
        assert res == {"cpu": cpu, "memory": memory}


def test_registry_uses_managed_identity():
    """レジストリ認証はパスワードではなくマネージド ID"""
    cfg = container_service_config(
        "example-api", IMAGE, ENV_ID, registry_server="example.azurecr.io"
    )
    registries = cfg["properties"]["configuration"]["registries"]
    assert registries == [{"server": "example.azurecr.io", "identity": "system"}]
    assert "password" not in json.dumps(cfg)


def test_no_registry_key_when_public_image():
    """レジストリを指定しなければ registries キーは作らない"""
    cfg = container_service_config("example-api", IMAGE, ENV_ID)
    assert "registries" not in cfg["properties"]["configuration"]


def test_env_is_sorted():
    """環境変数は名前順に並ぶ（同じ入力から同じリビジョンになる）"""
    cfg = container_service_config(
        "example-api", IMAGE, ENV_ID, env={"B": "2", "A": "1"}
    )
    assert cfg["properties"]["template"]["containers"][0]["env"] == [
        {"name": "A", "value": "1"},
        {"name": "B", "value": "2"},
    ]


def test_scale_to_zero_allowed():
    """min_replicas=0 はアイドル時の課金を止める設定として許す"""
    cfg = container_service_config("example-api", IMAGE, ENV_ID, min_replicas=0)
    assert cfg["properties"]["template"]["scale"] == {"minReplicas": 0, "maxReplicas": 10}


def test_invalid_inputs():
    """名前・イメージ・ポート・CPU・レプリカ数の不正は ValueError"""
    with pytest.raises(ValueError):
        container_service_config("Example_API", IMAGE, ENV_ID)
    with pytest.raises(ValueError):
        container_service_config("example-api", "example.azurecr.io/api", ENV_ID)
    with pytest.raises(ValueError, match="latest"):
        container_service_config("example-api", "example.azurecr.io/api:latest", ENV_ID)
    with pytest.raises(ValueError):
        container_service_config("example-api", IMAGE, ENV_ID, target_port=0)
    with pytest.raises(ValueError):
        container_service_config("example-api", IMAGE, ENV_ID, cpu=0.3)
    with pytest.raises(ValueError):
        container_service_config("example-api", IMAGE, ENV_ID, min_replicas=5, max_replicas=1)


def test_empty_tag_rejected():
    """コロンだけでタグが空のイメージは弾く"""
    with pytest.raises(ValueError, match="タグ"):
        container_service_config("example-api", "example.azurecr.io/api:", ENV_ID)


def test_digest_format_checked():
    """@ の後ろが sha256 の 64 桁でなければ弾く"""
    for bad in ("example.azurecr.io/api@", "example.azurecr.io/api@sha256:not-a-digest"):
        with pytest.raises(ValueError, match="ダイジェスト"):
            container_service_config("example-api", bad, ENV_ID)


def test_registry_identity_added_to_app():
    """レジストリをユーザー割り当て ID で引くなら、その ID をアプリにも付ける"""
    uami = (
        "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
        "/providers/Microsoft.ManagedIdentity/userAssignedIdentities/example-mi"
    )
    cfg = container_service_config(
        "example-api", IMAGE, ENV_ID, registry_server="example.azurecr.io",
        registry_identity=uami,
    )
    assert cfg["identity"] == {
        "type": "SystemAssigned, UserAssigned",
        "userAssignedIdentities": {uami: {}},
    }
    with pytest.raises(ValueError, match="registry_identity"):
        container_service_config("example-api", IMAGE, ENV_ID, registry_identity="example-mi")


def test_image_reference_grammar():
    """[HOST[:PORT]/]PATH[:TAG] の形を守る"""
    ok = [
        "example.azurecr.io/api:1",
        "localhost:5000/team/api:1",
        "example.azurecr.io/team/sub/api:1.4.2",
        "api:1",
    ]
    for image in ok:
        assert container_service_config("example-api", image, ENV_ID)
    for bad in ("api:1:2", "example.azurecr.io/API:1", "example.azurecr.io/api:@"):
        with pytest.raises(ValueError):
            container_service_config("example-api", bad, ENV_ID)


def test_registry_host_validated():
    """ホストとみなした部分の形式も見る"""
    for bad in (":5000/api:1", "-bad.example.com/api:1", "example.com:99999999/api:1"):
        with pytest.raises(ValueError):
            container_service_config("example-api", bad, ENV_ID)


def test_trailing_newline_rejected():
    """改行を含む参照は通さない。match だと改行の手前で止まる"""
    for bad in ("example.azurecr.io\n/api:1", "example.azurecr.io/api\n:1", "api:1\n"):
        with pytest.raises(ValueError):
            container_service_config("example-api", bad, ENV_ID)


def test_registry_port_range():
    """レジストリのポートは 1〜65535"""
    assert container_service_config("example-api", "localhost:65535/api:1", ENV_ID)
    for bad in ("localhost:0/api:1", "localhost:65536/api:1"):
        with pytest.raises(ValueError, match="ポート"):
            container_service_config("example-api", bad, ENV_ID)


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    env = {"A": "1"}
    before = copy.deepcopy(env)
    cfg = container_service_config("example-api", IMAGE, ENV_ID, env=env)
    assert env == before
    assert json.loads(json.dumps(cfg)) == cfg
