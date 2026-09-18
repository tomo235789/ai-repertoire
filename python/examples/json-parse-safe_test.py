"""json-parse-safe: try/except json.JSONDecodeError イディオムの Contract を検証する。"""

import json
import math
from decimal import Decimal

import pytest


def parse_safe(text: str) -> tuple[json.JSONDecodeError | None, object]:
    """失敗を (例外, None)、成功を (None, 値) で返す。"""
    try:
        return None, json.loads(text)
    except json.JSONDecodeError as e:
        return e, None


def test_success_returns_python_values() -> None:
    """解析できれば Python の値を返し、トップレベルの null / 数値 / 文字列も正当。"""
    assert parse_safe('{"name": "alice", "tags": [1, 2.5, true, null]}') == (
        None,
        {"name": "alice", "tags": [1, 2.5, True, None]},
    )
    assert parse_safe("null") == (None, None)
    assert parse_safe("1") == (None, 1)
    assert parse_safe('"s"') == (None, "s")
    assert parse_safe(' \n{"a": 1}\r\n') == (None, {"a": 1})


def test_failure_returns_json_decode_error() -> None:
    """構文の失敗は JSONDecodeError（ValueError のサブクラス）で、位置情報を持つ。"""
    err, value = parse_safe("{oops")
    assert value is None
    assert isinstance(err, json.JSONDecodeError)
    assert isinstance(err, ValueError)
    assert err.msg == "Expecting property name enclosed in double quotes"
    assert err.doc == "{oops"
    assert (err.pos, err.lineno, err.colno) == (1, 1, 2)
    assert str(err) == "Expecting property name enclosed in double quotes: line 1 column 2 (char 1)"


def test_inputs_that_fail() -> None:
    """失敗する入力の一覧。"""
    for text in (
        "",
        "undefined",
        "{a:1}",
        '{"a":1,}',
        "'x'",
        "nan",
        "inf",
        "01",
        "1.",
        ".5",
        '{"a":1}{"b":2}',
        '{"a":1}//c',
        '"\x01"',
        '﻿{"a":1}',
    ):
        err, _ = parse_safe(text)
        assert isinstance(err, json.JSONDecodeError), text
    assert parse_safe('{"a":1}{"b":2}')[0].msg == "Extra data"


def test_inputs_that_pass_but_need_care() -> None:
    """NaN / Infinity / 1e400 / 重複キー / 孤立サロゲートは通る。"""
    assert math.isnan(parse_safe("NaN")[1])
    assert parse_safe("Infinity")[1] == math.inf
    assert parse_safe("-Infinity")[1] == -math.inf
    assert parse_safe("1e400")[1] == math.inf
    assert parse_safe('{"a":1,"a":2}') == (None, {"a": 2})
    assert parse_safe('"\\ud800"') == (None, "\ud800")


def test_big_integers() -> None:
    """整数は桁落ちしないが、4300 桁超は JSONDecodeError ではない ValueError。"""
    assert parse_safe("12345678901234567890") == (None, 12345678901234567890)
    assert parse_safe("9007199254740993") == (None, 9007199254740993)
    with pytest.raises(ValueError) as info:
        parse_safe("1" * 5000)
    assert not isinstance(info.value, json.JSONDecodeError)


def test_non_string_input() -> None:
    """文字列以外は TypeError（except JSONDecodeError をすり抜ける）。bytes は可。"""
    with pytest.raises(TypeError):
        parse_safe(None)  # type: ignore[arg-type]
    assert json.loads(b'{"a": 1}') == {"a": 1}
    assert json.loads(bytearray(b"[1]")) == [1]


def test_hooks() -> None:
    """object_pairs_hook / parse_float / parse_int / parse_constant で値を差し替えられ、フック内の例外は伝わる。"""

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict:
        result: dict = {}
        for key, value in pairs:
            if key in result:
                raise ValueError(f"duplicate key: {key}")
            result[key] = value
        return result

    assert json.loads('{"a":1}', object_pairs_hook=reject_duplicates) == {"a": 1}
    with pytest.raises(ValueError, match="duplicate key: a"):
        json.loads('{"a":1,"a":2}', object_pairs_hook=reject_duplicates)
    assert json.loads("1.1", parse_float=Decimal) == Decimal("1.1")
    assert json.loads("12345678901234567890", parse_int=str) == "12345678901234567890"

    def reject_constant(name: str) -> object:
        raise ValueError(f"not allowed: {name}")

    with pytest.raises(ValueError, match="not allowed: NaN") as info:
        json.loads("NaN", parse_constant=reject_constant)
    assert not isinstance(info.value, json.JSONDecodeError)
    assert json.loads('{"at": "2020-01-01"}', object_hook=lambda d: {k: f"hooked:{v}" for k, v in d.items()}) == {
        "at": "hooked:2020-01-01"
    }


def test_result_is_untyped() -> None:
    """Pitfalls: 戻り値の形は保証されず、dict と決めつけると TypeError になる。"""
    _, value = parse_safe("[1]")
    with pytest.raises(TypeError):
        value["name"]  # type: ignore[index]
