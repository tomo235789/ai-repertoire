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

SA = "fn-runner@my-project.iam.gserviceaccount.com"
TOPIC = "projects/my-project/topics/orders"


def _cfg(**kw):
    kwargs = {"event_trigger_topic": TOPIC}
    kwargs.update(kw)
    return serverless_function_config(
        "example-fn", "python312", "handle", "example-bucket", "src.zip", SA, **kwargs
    )


def test_build_config():
    """ランタイムと入口とソースの場所が入る"""
    build = _cfg()["build_config"]
    assert build["runtime"] == "python312"
    assert build["entry_point"] == "handle"
    assert build["source"]["storage_source"] == {"bucket": "example-bucket", "object": "src.zip"}


def test_service_config_defaults():
    """既定は内部のみ、256Mi、60 秒"""
    service = _cfg()["service_config"]
    assert service["ingress_settings"] == "ALLOW_INTERNAL_ONLY"
    assert service["available_memory"] == "256Mi"
    assert service["timeout_seconds"] == 60
    assert service["service_account_email"] == SA
    assert service["vpc_connector_egress_settings"] == "PRIVATE_RANGES_ONLY"


def test_event_trigger_retry():
    """イベント関数は既定で再試行する"""
    trigger = _cfg()["event_trigger"]
    assert trigger["pubsub_topic"] == TOPIC
    assert trigger["retry_policy"] == "RETRY_POLICY_RETRY"
    trigger = _cfg(retry_on_failure=False)["event_trigger"]
    assert trigger["retry_policy"] == "RETRY_POLICY_DO_NOT_RETRY"


def test_http_function_has_no_trigger():
    """トピックを渡さなければ HTTP 関数。必須引数だけでも作れる"""
    cfg = serverless_function_config(
        "example-fn", "python312", "handle", "example-bucket", "src.zip", SA
    )
    assert "event_trigger" not in cfg
    # 再試行を明示すると HTTP 関数では弾かれる
    with pytest.raises(ValueError, match="HTTP 関数"):
        serverless_function_config(
            "example-fn", "python312", "handle", "example-bucket", "src.zip", SA,
            retry_on_failure=True,
        )


def test_timeout_limit_depends_on_trigger():
    """イベント関数は 540 秒、HTTP 関数は 3600 秒まで"""
    with pytest.raises(ValueError, match="540"):
        _cfg(timeout_seconds=541)
    assert serverless_function_config(
        "example-fn", "python312", "handle", "example-bucket", "src.zip", SA,
        timeout_seconds=3600,
    )["service_config"]["timeout_seconds"] == 3600


def test_env_sorted_and_secrets_rejected():
    """環境変数は名前順。秘密らしい名前は弾く"""
    env = _cfg(env={"B": "2", "A": "1"})["service_config"]["environment_variables"]
    assert list(env) == ["A", "B"]
    with pytest.raises(ValueError, match="秘密"):
        _cfg(env={"API_TOKEN": "abc"})


def test_retired_runtime_not_offered():
    """廃止済みのランタイムは選べない"""
    with pytest.raises(ValueError):
        serverless_function_config(
            "example-fn", "go122", "handle", "example-bucket", "src.zip", SA,
            event_trigger_topic=TOPIC,
        )


def test_invalid_inputs():
    """名前・ランタイム・入口・資源・数値・ingress の不正は ValueError"""
    with pytest.raises(ValueError):
        serverless_function_config("Example", "python312", "h", "b", "o", SA,
                                   event_trigger_topic=TOPIC)
    with pytest.raises(ValueError):
        serverless_function_config("example-fn", "ruby33", "h", "b", "o", SA,
                                   event_trigger_topic=TOPIC)
    with pytest.raises(ValueError):
        serverless_function_config("example-fn", "python312", "", "b", "o", SA,
                                   event_trigger_topic=TOPIC)
    with pytest.raises(ValueError):
        _cfg(memory="256MB")
    with pytest.raises(ValueError):
        _cfg(timeout_seconds=0)
    with pytest.raises(ValueError):
        _cfg(max_instances=0)
    with pytest.raises(ValueError):
        _cfg(ingress="PUBLIC")


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    env = {"A": "1"}
    before = copy.deepcopy(env)
    cfg = _cfg(env=env)
    assert env == before
    assert json.loads(json.dumps(cfg)) == cfg
