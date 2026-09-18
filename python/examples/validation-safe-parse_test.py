"""validation-safe-parse: try/except ValidationError イディオムの Contract を検証する。"""

import json

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError, field_validator


class Addr(BaseModel):
    city: str


class User(BaseModel):
    name: str
    age: int
    addr: Addr | None = None


def test_except_runs_once_with_all_failures() -> None:
    """失敗は ValidationError 1 つに全フィールド分がまとまり、成功時はモデルが得られる。"""
    caught: list[ValidationError] = []
    try:
        User.model_validate({"name": 1, "age": "x"})
    except ValidationError as e:
        caught.append(e)
    assert len(caught) == 1
    assert caught[0].error_count() == 2
    assert isinstance(caught[0], ValueError)

    try:
        user = User.model_validate({"name": "alice", "age": "20"})
    except ValidationError:
        pytest.fail("成功する入力で例外が出た")
    assert user.age == 20


def test_errors_structure() -> None:
    """errors() は type / loc / msg / input / url を持つ dict のリスト。include_url / include_input で外せる。"""
    with pytest.raises(ValidationError) as info:
        User.model_validate({"name": "a", "age": "x", "addr": {"city": 1}})
    err = info.value
    errors = err.errors()
    assert set(errors[0]) == {"type", "loc", "msg", "input", "url"}
    assert [(e["type"], e["loc"]) for e in errors] == [("int_parsing", ("age",)), ("string_type", ("addr", "city"))]
    assert errors[0]["input"] == "x"
    slim = err.errors(include_url=False, include_input=False)
    assert set(slim[0]) == {"type", "loc", "msg"}
    with pytest.raises(ValidationError) as info:
        User.model_validate(None)
    assert info.value.errors()[0]["loc"] == ()


def test_error_count_title_str_and_json() -> None:
    """error_count / title / str / json の形。"""
    with pytest.raises(ValidationError) as info:
        User.model_validate({"name": 1, "age": "x"})
    err = info.value
    assert err.error_count() == 2
    assert err.title == "User"
    assert str(err).splitlines()[0] == "2 validation errors for User"
    parsed = json.loads(err.json(include_url=False))
    assert parsed[0]["loc"] == ["name"]
    assert "url" not in parsed[0]
    assert "url" in json.loads(err.json())[0]


def test_same_rules_as_model_validate() -> None:
    """未知キーは無視され、入力は変更されない。"""
    src = {"name": "alice", "age": "20", "extra": True}
    user = User.model_validate(src)
    assert user.model_dump() == {"name": "alice", "age": 20, "addr": None}
    assert src == {"name": "alice", "age": "20", "extra": True}


def test_type_adapter_raises_same_error() -> None:
    """TypeAdapter でも失敗は同じ ValidationError。"""
    with pytest.raises(ValidationError) as info:
        TypeAdapter(list[int]).validate_python(["1", "x"])
    assert info.value.errors()[0]["loc"] == (1,)
    assert TypeAdapter(list[int]).validate_python(["1", 2]) == [1, 2]


def test_validator_exceptions_are_wrapped() -> None:
    """field_validator 内の ValueError / AssertionError は ValidationError に包まれ、TypeError は包まれない。"""

    class Checked(BaseModel):
        kind: str

        @field_validator("kind")
        @classmethod
        def check(cls, v: str) -> str:
            if v == "value":
                raise ValueError("bad value")
            if v == "assert":
                raise AssertionError("bad assert")
            if v == "type":
                raise TypeError("bad type")
            return v

    with pytest.raises(ValidationError) as info:
        Checked.model_validate({"kind": "value"})
    assert info.value.errors()[0]["type"] == "value_error"
    with pytest.raises(ValidationError) as info:
        Checked.model_validate({"kind": "assert"})
    assert info.value.errors()[0]["type"] == "assertion_error"
    with pytest.raises(TypeError):
        Checked.model_validate({"kind": "type"})


def test_result_tuple_idiom() -> None:
    """Pitfalls: success フラグ相当が欲しければ自分でタプルに詰める。"""

    def safe_parse(data: object) -> tuple[list[dict] | None, User | None]:
        try:
            return None, User.model_validate(data)
        except ValidationError as e:
            return e.errors(include_url=False), None

    errors, user = safe_parse({"name": "alice", "age": 20})
    assert errors is None
    assert user is not None and user.name == "alice"
    errors, user = safe_parse({"name": "alice"})
    assert user is None
    assert errors is not None and errors[0]["type"] == "missing"
