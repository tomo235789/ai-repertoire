"""カード queue-fanout-topic の Contract を検証するテスト"""

import copy
import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("queue-fanout-topic.py")
    spec = importlib.util.spec_from_file_location("queue_fanout_topic", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


fanout_topic = _load().fanout_topic

TOPIC = "projects/my-project/topics/orders"
BILLING = "projects/my-project/subscriptions/billing"
AUDIT = "projects/my-project/subscriptions/audit"
SA = "pusher@my-project.iam.gserviceaccount.com"


def test_subscriptions_sorted():
    """購読は名前順に並ぶ"""
    cfg = fanout_topic(TOPIC, {BILLING: {}, AUDIT: {}})
    assert [s["name"] for s in cfg["subscription_configs"]] == [AUDIT, BILLING]


def test_expiration_policy_is_empty():
    """使われない期間があっても購読が自動で消えないようにする"""
    cfg = fanout_topic(TOPIC, {AUDIT: {}})
    assert cfg["subscription_configs"][0]["expiration_policy"] == {}


def test_filter_is_opt_in():
    """フィルタは指定した購読だけに入る"""
    cfg = fanout_topic(TOPIC, {BILLING: {"filter": 'attributes.type = "order"'}, AUDIT: {}})
    configs = {s["name"]: s for s in cfg["subscription_configs"]}
    assert configs[BILLING]["filter"] == 'attributes.type = "order"'
    assert "filter" not in configs[AUDIT]


def test_push_requires_oidc_token():
    """プッシュ配信は OIDC トークンで署名する"""
    cfg = fanout_topic(
        TOPIC, {BILLING: {"push_endpoint": "https://example.com/hook", "push_service_account": SA}}
    )
    push = cfg["subscription_configs"][0]["push_config"]
    assert push["push_endpoint"] == "https://example.com/hook"
    assert push["oidc_token"] == {"service_account_email": SA}


def test_push_validation():
    """HTTP のエンドポイントとサービスアカウント無しは ValueError"""
    with pytest.raises(ValueError, match="HTTPS"):
        fanout_topic(
            TOPIC, {BILLING: {"push_endpoint": "http://example.com", "push_service_account": SA}}
        )
    with pytest.raises(ValueError, match="サービスアカウント"):
        fanout_topic(TOPIC, {BILLING: {"push_endpoint": "https://example.com/hook"}})


def test_topic_options():
    """スキーマと暗号鍵は渡したときだけ入る"""
    cfg = fanout_topic(TOPIC, {AUDIT: {}})["topic_config"]
    assert cfg["message_retention_duration"] == {"seconds": 86400}
    assert "schema_settings" not in cfg
    assert "kms_key_name" not in cfg
    cfg = fanout_topic(
        TOPIC, {AUDIT: {}}, schema="projects/my-project/schemas/order", kms_key_name="k"
    )["topic_config"]
    assert cfg["schema_settings"] == {"schema": "projects/my-project/schemas/order", "encoding": "JSON"}
    assert cfg["kms_key_name"] == "k"


def test_goog_prefixed_ids_rejected():
    """Pub/Sub の ID は goog で始められない"""
    with pytest.raises(ValueError, match="goog"):
        fanout_topic("projects/my-project/topics/googevents", {AUDIT: {}})


def test_push_arguments_must_be_paired():
    """プッシュ配信は配信先と署名するサービスアカウントを対で指定する"""
    with pytest.raises(ValueError, match="対で指定"):
        fanout_topic(TOPIC, {BILLING: {"push_service_account": SA}})


def test_invalid_inputs():
    """名前・購読者・保持日数・設定キーの不正は ValueError"""
    with pytest.raises(ValueError):
        fanout_topic("orders", {AUDIT: {}})
    with pytest.raises(ValueError):
        fanout_topic(TOPIC, {})
    with pytest.raises(ValueError):
        fanout_topic(TOPIC, {"audit": {}})
    with pytest.raises(ValueError):
        fanout_topic(TOPIC, {AUDIT: {}}, message_retention_days=32)
    with pytest.raises(ValueError, match="未知の設定キー"):
        fanout_topic(TOPIC, {AUDIT: {"retry": True}})


def test_pure_and_serializable():
    """引数を変更せず、返り値は JSON にできる"""
    subscribers = {AUDIT: {"filter": "true"}}
    before = copy.deepcopy(subscribers)
    cfg = fanout_topic(TOPIC, subscribers)
    assert subscribers == before
    assert json.loads(json.dumps(cfg)) == cfg
