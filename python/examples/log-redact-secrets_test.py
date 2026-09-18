"""log-redact-secrets: キー名でマスクする純粋関数 redact の Contract を検証する。"""

import io
import logging
from collections.abc import Iterable
from datetime import datetime
from typing import Any

import pytest

DEFAULT_KEYS = ("password", "token", "authorization", "secret", "api_key", "cookie")


def redact(obj: Any, keys: Iterable[str] = DEFAULT_KEYS, mask: str = "[REDACTED]") -> Any:
    """カードの Usage と同じ関数。"""
    lower = {k.lower() for k in keys}  # ジェネレータを渡されても最初に 1 度だけ実体化する

    def walk(value: Any) -> Any:
        if isinstance(value, dict):
            return {k: mask if str(k).lower() in lower else walk(v) for k, v in value.items()}
        if isinstance(value, list):
            return [walk(v) for v in value]
        return value

    return walk(obj)


def test_masks_nested_dicts_and_lists() -> None:
    """ネストした辞書・リストの中の一致キーをすべて置き換える。"""
    src = {"user": "a", "password": "p", "headers": {"Authorization": "Bearer x"}, "items": [{"token": "t"}, {"id": 1}]}
    assert redact(src) == {
        "user": "a",
        "password": "[REDACTED]",
        "headers": {"Authorization": "[REDACTED]"},
        "items": [{"token": "[REDACTED]"}, {"id": 1}],
    }


def test_key_match_is_case_insensitive_and_exact() -> None:
    """大文字小文字は無視し、部分一致はしない。str でないキーは str にして比較する。"""
    assert redact({"AUTHORIZATION": 1, "Token": 2, "password_hash": 3}) == {"AUTHORIZATION": "[REDACTED]", "Token": "[REDACTED]", "password_hash": 3}
    assert redact({1: "x", "1": "y"}, keys=["1"]) == {1: "[REDACTED]", "1": "[REDACTED]"}


def test_masks_any_value_type_including_none_and_containers() -> None:
    """一致したキーの値は型を問わず丸ごと置き換える。"""
    assert redact({"token": None, "secret": {"a": 1}, "cookie": [1, 2], "password": 0}) == {
        "token": "[REDACTED]",
        "secret": "[REDACTED]",
        "cookie": "[REDACTED]",
        "password": "[REDACTED]",
    }


def test_does_not_mutate_input_and_returns_new_containers() -> None:
    """入力を変更せず、dict / list は新しいオブジェクトを返す。それ以外は同じオブジェクト。"""
    when = datetime(2024, 1, 1)
    src = {"password": "p", "headers": {"x": 1}, "items": [1], "when": when, "pair": (1, {"token": "t"})}
    out = redact(src)
    assert src["password"] == "p"
    assert out is not src
    assert out["headers"] is not src["headers"] and out["headers"] == src["headers"]
    assert out["items"] is not src["items"]
    assert out["when"] is when
    assert out["pair"] is src["pair"]
    assert out["pair"][1]["token"] == "t"  # tuple の中は辿らない


def test_empty_keys_copies_structure_only() -> None:
    """keys が空なら何も置き換えず、構造だけコピーする。"""
    src = {"password": "p", "nested": {"token": "t"}}
    out = redact(src, keys=[])
    assert out == src
    assert out is not src and out["nested"] is not src["nested"]


def test_custom_mask_and_scalar_passthrough() -> None:
    """mask は差し替えられ、辞書でもリストでもない入力はそのまま返る。"""
    assert redact({"password": "p"}, mask="***") == {"password": "***"}
    assert redact("plain") == "plain"
    assert redact(42) == 42


def test_cycle_raises_recursion_error() -> None:
    """循環参照があると RecursionError。"""
    cyclic: dict[str, Any] = {}
    cyclic["self"] = cyclic
    with pytest.raises(RecursionError):
        redact(cyclic)


class RedactFilter(logging.Filter):
    """Alternatives: record.args をマスクする Filter。辞書 1 つなら args はその辞書自体。"""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.args, dict):
            record.args = redact(record.args)
        elif record.args:
            record.args = tuple(redact(a) for a in record.args)
        return True


def test_logging_filter_masks_args_but_not_fstring() -> None:
    """Filter で % 引数はマスクされ、f-string で埋め込んだ値はマスクされない。"""
    buffer = io.StringIO()
    handler = logging.StreamHandler(buffer)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("app.redact")
    logger.handlers[:] = [handler]
    logger.propagate = False
    logger.addFilter(RedactFilter())
    data = {"user": "a", "password": "p"}
    logger.warning("login %s", data)
    logger.warning("login %s %s", data, {"token": "t"})
    logger.warning(f"login {data}")
    logger.handlers[:] = []
    logger.filters[:] = []
    out = buffer.getvalue().splitlines()
    assert out[0] == "login {'user': 'a', 'password': '[REDACTED]'}"
    assert out[1] == "login {'user': 'a', 'password': '[REDACTED]'} {'token': '[REDACTED]'}"
    assert out[2] == "login {'user': 'a', 'password': 'p'}"
    assert data == {"user": "a", "password": "p"}
