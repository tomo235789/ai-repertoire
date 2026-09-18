"""カード observability-structured-logs の Contract を検証するテスト"""

import json
from pathlib import Path
import importlib.util

import pytest


def _load():
    path = Path(__file__).with_name("observability-structured-logs.py")
    spec = importlib.util.spec_from_file_location("observability_structured_logs", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_mod = _load()
log_line = _mod.log_line
diagnostic_setting = _mod.diagnostic_setting

TS = "2026-09-18T01:02:03Z"
WORKSPACE = (
    "/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/example-rg"
    "/providers/Microsoft.OperationalInsights/workspaces/example-law"
)


def test_log_line_is_single_line_json():
    """1 行の JSON で、キーは名前順に並ぶ"""
    line = log_line(TS, "Information", "注文を受け付けた", fields={"orderId": "A-1"})
    assert "\n" not in line
    assert json.loads(line) == {
        "message": "注文を受け付けた",
        "orderId": "A-1",
        "severity": "Information",
        "timestamp": TS,
    }
    assert list(json.loads(line)) == sorted(json.loads(line))


def test_secret_fields_are_redacted():
    """秘密らしいキーは値ごと伏せる"""
    record = json.loads(
        log_line(TS, "Information", "接続", fields={"password": "p@ss", "Token": "abc", "user": "u"})
    )
    assert record["password"] == "[REDACTED]"
    assert record["Token"] == "[REDACTED]"
    assert record["user"] == "u"


def test_redaction_is_recursive():
    """入れ子の dict と list の中も伏せる"""
    record = json.loads(
        log_line(
            TS, "Information", "要求",
            fields={"request": {"headers": {"authorization": "Bearer x"}, "path": "/items"},
                    "items": [{"token": "t1"}, {"id": 1}]},
        )
    )
    assert record["request"]["headers"]["authorization"] == "[REDACTED]"
    assert record["request"]["path"] == "/items"
    assert record["items"] == [{"token": "[REDACTED]"}, {"id": 1}]


def test_reserved_keys_rejected():
    """関数が埋めるキーは追加項目で上書きできない"""
    for key in ("timestamp", "severity", "message", "operationId"):
        with pytest.raises(ValueError, match="予約キー"):
            log_line(TS, "Information", "x", fields={key: "上書き"})


def test_operation_id_included_when_given():
    """相関 ID は渡したときだけ入る"""
    assert "operationId" not in json.loads(log_line(TS, "Error", "失敗"))
    assert json.loads(log_line(TS, "Error", "失敗", operation_id="op-1"))["operationId"] == "op-1"


def test_non_ascii_not_escaped():
    """日本語はエスケープせずそのまま入る"""
    assert "注文" in log_line(TS, "Information", "注文")


def test_log_line_validation():
    """タイムスタンプ・重大度・本文の不正は ValueError"""
    with pytest.raises(ValueError):
        log_line("2026/09/18", "Information", "x")
    with pytest.raises(ValueError):
        log_line(TS, "INFO", "x")
    with pytest.raises(ValueError):
        log_line(TS, "Information", "")
    with pytest.raises(ValueError):
        log_line(TS, "Information", "x" * (32 * 1024 + 1))


def test_diagnostic_setting_uses_dedicated_tables():
    """専用テーブルに入れる"""
    cfg = diagnostic_setting(WORKSPACE, ["AppServiceHTTPLogs"])
    assert cfg["logAnalyticsDestinationType"] == "Dedicated"
    assert cfg["workspaceId"] == WORKSPACE


def test_categories_sorted_and_deduplicated():
    """カテゴリは重複を除いて名前順に並ぶ"""
    cfg = diagnostic_setting(WORKSPACE, ["B", "A", "A"])
    assert [entry["category"] for entry in cfg["logs"]] == ["A", "B"]


def test_metrics_can_be_disabled():
    """メトリックは切れる"""
    assert diagnostic_setting(WORKSPACE, ["A"], metrics=False)["metrics"] == []
    assert diagnostic_setting(WORKSPACE, ["A"])["metrics"] == [
        {"category": "AllMetrics", "enabled": True}
    ]


def test_no_retention_policy_in_diagnostic_setting():
    """保持期間は診断設定では決まらないので、そのキーを作らない"""
    cfg = diagnostic_setting(WORKSPACE, ["A"])
    assert "retentionPolicy" not in cfg["logs"][0]
    assert cfg["logs"][0] == {"category": "A", "enabled": True}


def test_diagnostic_setting_validation():
    """ワークスペース ID・カテゴリ・保持日数の不正は ValueError"""
    with pytest.raises(ValueError):
        diagnostic_setting("example-law", ["A"])
    with pytest.raises(ValueError):
        diagnostic_setting(WORKSPACE, [])



def test_redaction_normalizes_key_spelling():
    """区切り文字と大文字小文字が違っても伏せる"""
    record = json.loads(
        log_line(TS, "Information", "x",
                 fields={"accessToken": "a", "x-api-key": "b", "client_secret": "c", "note": "d"})
    )
    assert record["accessToken"] == "[REDACTED]"
    assert record["x-api-key"] == "[REDACTED]"
    assert record["client_secret"] == "[REDACTED]"
    assert record["note"] == "d"


def test_pure_and_serializable():
    """同じ入力に同じ出力を返し、JSON にできる"""
    a = diagnostic_setting(WORKSPACE, ["A"])
    assert a == diagnostic_setting(WORKSPACE, ["A"])
    assert json.loads(json.dumps(a)) == a
    assert log_line(TS, "Information", "x") == log_line(TS, "Information", "x")
