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

IMAGE = "asia-northeast1-docker.pkg.dev/my-project/app/api:1.4.2"
SA = "app-runner@my-project.iam.gserviceaccount.com"


def _cfg(**kw):
    return container_service_config("example-api", IMAGE, SA, **kw)


def test_ingress_is_restricted_by_default():
    """既定ではロードバランサ経由だけ"""
    assert _cfg()["service"]["ingress"] == "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"


def test_unauthenticated_is_opt_in():
    """認証なしの呼び出しは明示したときだけ"""
    assert _cfg()["iam_policy"] == {"bindings": []}
    policy = _cfg(allow_unauthenticated=True)["iam_policy"]
    assert policy["bindings"] == [{"role": "roles/run.invoker", "members": ["allUsers"]}]


def test_scaling_and_concurrency():
    """スケールと同時実行数はそのまま入る"""
    template = _cfg(min_instances=1, max_instances=10, concurrency=40)["service"]["template"]
    assert template["scaling"] == {"min_instance_count": 1, "max_instance_count": 10}
    assert template["max_instance_request_concurrency"] == 40


def test_service_id_returned():
    """作成時に渡す ID を本体とは別に返す"""
    assert _cfg()["service_id"] == "example-api"


def test_service_account_required_in_template():
    """実行に使うサービスアカウントが必ず入る"""
    assert _cfg()["service"]["template"]["service_account"] == SA


def test_env_sorted_and_secrets_rejected():
    """環境変数は名前順。秘密らしい名前は弾く"""
    env = _cfg(env={"B": "2", "A": "1"})["service"]["template"]["containers"][0]["env"]
    assert env == [{"name": "A", "value": "1"}, {"name": "B", "value": "2"}]
    with pytest.raises(ValueError, match="秘密"):
        _cfg(env={"DB_PASSWORD": "p@ss"})


def test_vpc_access_is_opt_in():
    """VPC コネクタは渡したときだけ。送信は内部レンジだけに絞る"""
    assert "vpc_access" not in _cfg()["service"]["template"]
    access = _cfg(vpc_connector="projects/p/locations/l/connectors/c")["service"]["template"][
        "vpc_access"
    ]
    assert access["egress"] == "PRIVATE_RANGES_ONLY"


def test_digest_image_allowed():
    """ダイジェスト指定のイメージも通る"""
    digest = "asia-northeast1-docker.pkg.dev/my-project/app/api@sha256:" + "a" * 64
    assert container_service_config("example-api", digest, SA)["service"]["template"][
        "containers"
    ][0]["image"] == digest


def test_invalid_inputs():
    """名前・イメージ・資源・数値・ingress の不正は ValueError"""
    with pytest.raises(ValueError):
        container_service_config("Example_API", IMAGE, SA)
    with pytest.raises(ValueError):
        container_service_config("example-api", "app/api", SA)
    with pytest.raises(ValueError, match="latest"):
        container_service_config("example-api", "app/api:latest", SA)
    with pytest.raises(ValueError):
        container_service_config("example-api", IMAGE, "app-runner")
    with pytest.raises(ValueError):
        _cfg(cpu="one")
    with pytest.raises(ValueError):
        _cfg(memory="512MB")
    with pytest.raises(ValueError):
        _cfg(min_instances=5, max_instances=1)
    with pytest.raises(ValueError):
        _cfg(concurrency=0)
    with pytest.raises(ValueError):
        _cfg(ingress="PUBLIC")


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    env = {"A": "1"}
    before = copy.deepcopy(env)
    cfg = _cfg(env=env)
    assert env == before
    assert json.loads(json.dumps(cfg)) == cfg
