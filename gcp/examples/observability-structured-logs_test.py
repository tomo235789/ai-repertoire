"""カード observability-structured-logs の Contract を検証するテスト"""

import importlib.util
import json
from pathlib import Path

import pytest


def _load():
    path = Path(__file__).with_name("observability-structured-logs.py")
    spec = importlib.util.spec_from_file_location("observability_structured_logs", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load()
log_line = _mod.log_line
log_sink = _mod.log_sink

TS = "2026-09-18T01:02:03Z"
BUCKET_DEST = "storage.googleapis.com/example-log-bucket"
BQ_DEST = "bigquery.googleapis.com/projects/my-project/datasets/logs"


def test_log_line_uses_logging_keys():
    """Cloud Logging が読むキー名で出す"""
    record = json.loads(log_line(TS, "INFO", "注文を受け付けた"))
    assert record == {"time": TS, "severity": "INFO", "message": "注文を受け付けた"}


def test_trace_key():
    """トレースは専用のキーに入る"""
    record = json.loads(log_line(TS, "INFO", "x", trace="projects/my-project/traces/abc"))
    assert record["logging.googleapis.com/trace"] == "projects/my-project/traces/abc"


def test_secret_fields_redacted():
    """秘密らしいキーは値ごと伏せる"""
    record = json.loads(log_line(TS, "INFO", "接続", fields={"password": "p@ss", "user": "u"}))
    assert record["password"] == "[REDACTED]"
    assert record["user"] == "u"


def test_reserved_keys_rejected():
    """予約キーは追加項目に入れられない"""
    with pytest.raises(ValueError, match="予約キー"):
        log_line(TS, "INFO", "x", fields={"severity": "ERROR"})


def test_log_line_validation():
    """タイムスタンプ・重大度・本文の不正は ValueError"""
    with pytest.raises(ValueError):
        log_line("2026/09/18", "INFO", "x")
    with pytest.raises(ValueError):
        log_line(TS, "Information", "x")
    with pytest.raises(ValueError):
        log_line(TS, "INFO", "")


def test_sink_exclusions_sorted():
    """除外は名前順に並び、いずれも有効"""
    sink = log_sink(
        "to-bucket", BUCKET_DEST, 'severity >= "WARNING"',
        exclusions={"b-noise": "textPayload:\"ping\"", "a-health": "textPayload:\"/healthz\""},
    )
    assert [e["name"] for e in sink["exclusions"]] == ["a-health", "b-noise"]
    assert all(e["disabled"] is False for e in sink["exclusions"])


def test_bigquery_options_only_for_bigquery():
    """分割テーブルの指定は BigQuery 転送のときだけ"""
    assert "bigquery_options" not in log_sink("s", BUCKET_DEST, "true")
    sink = log_sink("s", BQ_DEST, "true")
    assert sink["bigquery_options"] == {"use_partitioned_tables": True}


def test_redaction_is_recursive():
    """入れ子の dict と list の中も伏せる"""
    record = json.loads(
        log_line(
            TS, "INFO", "要求",
            fields={"request": {"headers": {"authorization": "Bearer x"}, "path": "/items"},
                    "items": [{"token": "t1"}, {"id": 1}]},
        )
    )
    assert record["request"]["headers"]["authorization"] == "[REDACTED]"
    assert record["request"]["path"] == "/items"
    assert record["items"] == [{"token": "[REDACTED]"}, {"id": 1}]


def test_sink_destination_must_be_known():
    """転送先は Cloud Logging が受け付ける形式だけ"""
    with pytest.raises(ValueError, match="転送先"):
        log_sink("s", "example.invalid/resource", "true")
    for dest in (BUCKET_DEST, BQ_DEST, "pubsub.googleapis.com/projects/p/topics/t"):
        assert log_sink("s", dest, "true")["destination"] == dest


def test_sink_validation():
    """名前・転送先・フィルタの不正は ValueError"""
    with pytest.raises(ValueError):
        log_sink("", BUCKET_DEST, "true")
    with pytest.raises(ValueError):
        log_sink("s", "example-log-bucket", "true")
    with pytest.raises(ValueError, match="費用"):
        log_sink("s", BUCKET_DEST, "")


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    assert log_line(TS, "INFO", "x") == log_line(TS, "INFO", "x")
    sink = log_sink("s", BUCKET_DEST, "true")
    assert json.loads(json.dumps(sink)) == sink
