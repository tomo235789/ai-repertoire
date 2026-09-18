"""log-structured: logging.Formatter を継承した JSON 出力の Contract を検証する。"""

import io
import json
import logging
from collections.abc import Iterator
from datetime import datetime, timezone

import pytest


class JsonFormatter(logging.Formatter):
    """カードの Usage と同じクラス。"""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": datetime.fromtimestamp(record.created, timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False, default=str)


STANDARD_ATTRS = set(logging.LogRecord("x", logging.INFO, "", 0, "", (), None).__dict__) | {"message", "asctime"}


class JsonWithExtraFormatter(JsonFormatter):
    """Alternatives: extra の値をすべて出す。"""

    def format(self, record: logging.LogRecord) -> str:
        entry = json.loads(super().format(record))
        entry.update({k: v for k, v in record.__dict__.items() if k not in STANDARD_ATTRS})
        return json.dumps(entry, ensure_ascii=False, default=str)


@pytest.fixture
def logger_and_buffer() -> Iterator[tuple[logging.Logger, io.StringIO]]:
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(JsonFormatter())
    logger = logging.getLogger("app.test")
    logger.handlers[:] = [handler]
    logger.setLevel(logging.DEBUG)
    logger.propagate = False
    yield logger, buffer
    logger.handlers[:] = []


def lines(buffer: io.StringIO) -> list[dict]:
    return [json.loads(line) for line in buffer.getvalue().splitlines()]


def test_one_json_per_line_with_formatted_message(logger_and_buffer: tuple[logging.Logger, io.StringIO]) -> None:
    """1 行 1 JSON で、msg は % 書式を適用した文字列。改行はエスケープされる。"""
    logger, buffer = logger_and_buffer
    logger.info("GET %s %d", "/items", 200)
    logger.warning("複数行\nのメッセージ")
    raw = buffer.getvalue()
    assert raw.count("\n") == 2
    first, second = lines(buffer)
    assert first["msg"] == "GET /items 200"
    assert (first["level"], first["logger"]) == ("INFO", "app.test")
    assert second["msg"] == "複数行\nのメッセージ"
    assert "\\n" in raw and "複数行" in raw


def test_time_is_aware_utc_iso8601(logger_and_buffer: tuple[logging.Logger, io.StringIO]) -> None:
    """time は record.created（epoch 秒）を UTC にした ISO 8601 で、+00:00 付き。"""
    logger, buffer = logger_and_buffer
    before = datetime.now(timezone.utc)
    logger.info("t")
    after = datetime.now(timezone.utc)
    stamp = datetime.fromisoformat(lines(buffer)[0]["time"])
    assert stamp.tzinfo is not None
    assert lines(buffer)[0]["time"].endswith("+00:00")
    assert before.replace(microsecond=0) <= stamp <= after


def test_exception_is_expanded_with_traceback_and_cause(logger_and_buffer: tuple[logging.Logger, io.StringIO]) -> None:
    """logger.exception は exc_info を持ち、formatException で traceback（連鎖込み）の文字列になる。"""
    logger, buffer = logger_and_buffer
    try:
        try:
            int("x")
        except ValueError as err:
            raise RuntimeError("wrap") from err
    except RuntimeError:
        logger.exception("failed")
    entry = lines(buffer)[0]
    assert entry["level"] == "ERROR"
    assert entry["exc"].startswith("Traceback (most recent call last):")
    assert "ValueError: invalid literal" in entry["exc"]
    assert "The above exception was the direct cause" in entry["exc"]
    assert entry["exc"].rstrip().endswith("RuntimeError: wrap")


def test_extra_becomes_record_attribute_and_collision_is_key_error(logger_and_buffer: tuple[logging.Logger, io.StringIO]) -> None:
    """extra は record の属性になり、既存属性名と衝突すると KeyError。"""
    logger, buffer = logger_and_buffer
    logger.handlers[0].setFormatter(JsonWithExtraFormatter())
    logger.info("with extra", extra={"user_id": 7, "when": datetime(2024, 1, 1)})
    entry = lines(buffer)[0]
    assert entry["user_id"] == 7
    assert entry["when"] == "2024-01-01 00:00:00"
    with pytest.raises(KeyError, match="Attempt to overwrite 'msg' in LogRecord"):
        logger.info("bad", extra={"msg": "x"})


def test_record_msg_keeps_format_string(logger_and_buffer: tuple[logging.Logger, io.StringIO]) -> None:
    """record.msg は書式文字列のまま、getMessage() が args を適用する。f-string だと args が空。"""
    records: list[logging.LogRecord] = []
    logger, _ = logger_and_buffer
    logger.addFilter(lambda record: records.append(record) or True)
    logger.info("GET %s", "/a")
    logger.info(f"GET {'/b'}")
    assert (records[0].msg, records[0].args, records[0].getMessage()) == ("GET %s", ("/a",), "GET /a")
    assert (records[1].msg, records[1].args) == ("GET /b", ())


def test_unserializable_value_without_default_is_logging_error(capsys: pytest.CaptureFixture[str]) -> None:
    """default=str が無いと json.dumps が TypeError になり、stderr に --- Logging error --- が出て例外は伝わらない。"""

    class StrictJsonFormatter(logging.Formatter):
        def format(self, record: logging.LogRecord) -> str:
            return json.dumps({"msg": record.getMessage(), "obj": getattr(record, "obj", None)})

    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(StrictJsonFormatter())
    logger = logging.getLogger("app.strict")
    logger.handlers[:] = [handler]
    logger.propagate = False
    logger.warning("x", extra={"obj": object()})
    logger.handlers[:] = []
    assert buffer.getvalue() == ""
    assert "--- Logging error ---" in capsys.readouterr().err


def test_ensure_ascii_default_escapes_japanese() -> None:
    """Pitfalls: json.dumps の既定は ensure_ascii=True で日本語がエスケープされる。"""
    assert json.dumps({"m": "日本"}) == '{"m": "\\u65e5\\u672c"}'
    assert json.dumps({"m": "日本"}, ensure_ascii=False) == '{"m": "日本"}'
