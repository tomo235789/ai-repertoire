"""validation-coerce-number: TypeAdapter による数値変換の Contract を検証する。"""

import math
from decimal import Decimal
from typing import Annotated

import pytest
from pydantic import Field, TypeAdapter, ValidationError

Int = TypeAdapter(int)
Float = TypeAdapter(float)
Port = TypeAdapter(Annotated[int, Field(ge=1, le=65535)])


def error_type(adapter: TypeAdapter, value: object, **kwargs: object) -> str:
    """失敗の type を返す。"""
    with pytest.raises(ValidationError) as info:
        adapter.validate_python(value, **kwargs)
    return info.value.errors()[0]["type"]


def test_int_lax_conversions() -> None:
    """10 進整数の文字列・小数部 0 の float / Decimal / 文字列・bool・bytes は int になる。"""
    assert Int.validate_python("12") == 12
    assert Int.validate_python(" 12 ") == 12
    assert Int.validate_python("+12") == 12
    assert Int.validate_python("-12") == -12
    assert Int.validate_python("1_000") == 1000
    assert Int.validate_python("0012") == 12
    assert Int.validate_python(12.0) == 12
    assert Int.validate_python("12.0") == 12
    assert Int.validate_python(Decimal("12.0")) == 12
    assert Int.validate_python(True) == 1
    assert Int.validate_python(False) == 0
    assert Int.validate_python(b"12") == 12
    assert type(Int.validate_python(12.0)) is int


def test_int_failures() -> None:
    """空文字・小数・指数・16 進・全角・NaN・None は失敗し、type が分かれる。"""
    for value in ("", "  ", "12.5", "1e3", "0x10", "abc", "１２", "12 34"):
        assert error_type(Int, value) == "int_parsing"
    assert error_type(Int, 12.5) == "int_from_float"
    assert error_type(Int, Decimal("12.5")) == "int_from_float"
    assert error_type(Int, math.nan) == "finite_number"
    assert error_type(Int, math.inf) == "finite_number"
    assert error_type(Int, None) == "int_type"
    assert error_type(Int, []) == "int_type"


def test_float_lax_conversions() -> None:
    """float は指数表記や区切り付きも通し、inf / nan も既定で通る。"""
    assert Float.validate_python("12") == 12.0
    assert Float.validate_python("1e3") == 1000.0
    assert Float.validate_python(" 1.5 ") == 1.5
    assert Float.validate_python("1_000.5") == 1000.5
    assert Float.validate_python(True) == 1.0
    assert Float.validate_python("inf") == math.inf
    assert Float.validate_python("Infinity") == math.inf
    assert math.isnan(Float.validate_python("nan"))
    for value in ("", "0x10", "abc"):
        assert error_type(Float, value) == "float_parsing"
    assert error_type(Float, None) == "float_type"
    finite = TypeAdapter(Annotated[float, Field(allow_inf_nan=False)])
    assert finite.validate_python("1.5") == 1.5
    assert error_type(finite, "inf") == "finite_number"


def test_strict_rejects_conversion() -> None:
    """strict=True / Field(strict=True) は変換せず、int_type で失敗する。"""
    for value in ("12", 12.0, True):
        assert error_type(Int, value, strict=True) == "int_type"
    assert Int.validate_python(12, strict=True) == 12
    strict = TypeAdapter(Annotated[int, Field(strict=True)])
    assert error_type(strict, "12") == "int_type"


def test_big_integers_are_kept() -> None:
    """桁数の上限は無く、多倍長 int になる。"""
    assert Int.validate_python("99999999999999999999999999") == 99999999999999999999999999
    assert Int.validate_python(10**30) == 10**30


def test_constraints_apply_after_conversion() -> None:
    """Field の範囲制約は変換後の値に対して行う。"""
    assert Port.validate_python("8080") == 8080
    assert error_type(Port, "0") == "greater_than_equal"
    assert error_type(Port, "70000") == "less_than_equal"
    assert error_type(Port, "") == "int_parsing"


def test_optional_keeps_none_but_rejects_empty() -> None:
    """int | None は None をそのまま通し、空文字は失敗する。"""
    optional = TypeAdapter(int | None)
    assert optional.validate_python(None) is None
    assert optional.validate_python("1") == 1
    with pytest.raises(ValidationError):
        optional.validate_python("")


def test_json_and_strings_modes() -> None:
    """validate_json / validate_strings でも同じ変換規則。"""
    assert Int.validate_json("12") == 12
    assert Int.validate_json('"12"') == 12
    assert Int.validate_strings("12") == 12


def test_builtin_int_differs() -> None:
    """Alternatives: int(s) は "12.0" を受け付けず、" 12 " は通る。"""
    assert int(" 12 ") == 12
    with pytest.raises(ValueError):
        int("12.0")
