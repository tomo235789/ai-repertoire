"""validation-parse-schema: BaseModel.model_validate の Contract を検証する。"""

from typing import Annotated

import pytest
from pydantic import BaseModel, ConfigDict, Field, ValidationError


class Addr(BaseModel):
    city: str


class User(BaseModel):
    name: str
    age: int
    tags: list[int] = []
    addr: Addr | None = None


def test_returns_new_model_instance() -> None:
    """成功するとモデルのインスタンスを返し、ネストした値も新しく作られる。"""
    src = {"name": "alice", "age": 20, "tags": [1], "addr": {"city": "tokyo"}}
    user = User.model_validate(src)
    assert isinstance(user, User)
    assert user.age == 20
    assert user.tags == [1]
    assert user.tags is not src["tags"]
    assert isinstance(user.addr, Addr)
    assert user.addr is not src["addr"]


def test_does_not_mutate_input() -> None:
    """入力の dict を変更しない。未知キーの除去も型変換も返り値の側だけ。"""
    src = {"name": "alice", "age": "20", "extra": True}
    User.model_validate(src)
    assert src == {"name": "alice", "age": "20", "extra": True}


def test_validation_error_collects_all_failures() -> None:
    """失敗は ValidationError（ValueError のサブクラス）で、errors() に全項目がまとまる。"""
    with pytest.raises(ValidationError) as info:
        User.model_validate({"name": 1, "age": "x", "tags": [1, "y"], "addr": {"city": 2}})
    err = info.value
    assert isinstance(err, ValueError)
    errors = err.errors(include_url=False)
    assert [(e["type"], e["loc"]) for e in errors] == [
        ("string_type", ("name",)),
        ("int_parsing", ("age",)),
        ("int_parsing", ("tags", 1)),
        ("string_type", ("addr", "city")),
    ]
    assert errors[0]["input"] == 1
    assert "url" in err.errors()[0]
    assert "url" not in errors[0]


def test_unknown_keys_are_ignored_by_default() -> None:
    """未知キーは既定で無視、extra="forbid" で失敗、extra="allow" で残る。"""
    user = User.model_validate({"name": "alice", "age": 20, "extra": True})
    assert user.model_extra is None
    assert user.model_dump() == {"name": "alice", "age": 20, "tags": [], "addr": None}

    class Forbid(BaseModel):
        model_config = ConfigDict(extra="forbid")
        name: str

    class Allow(BaseModel):
        model_config = ConfigDict(extra="allow")
        name: str

    with pytest.raises(ValidationError) as info:
        Forbid.model_validate({"name": "alice", "extra": True})
    assert info.value.errors()[0]["type"] == "extra_forbidden"
    assert info.value.errors()[0]["loc"] == ("extra",)
    allowed = Allow.model_validate({"name": "alice", "extra": True})
    assert allowed.model_extra == {"extra": True}
    assert allowed.model_dump() == {"name": "alice", "extra": True}


def test_lax_mode_converts_types() -> None:
    """既定の lax モードは "20" / 20.0 / True / b"20" を int に変換し、20.5 と "1e3" は失敗する。"""
    for raw in ("20", 20.0, b"20"):
        assert User.model_validate({"name": "a", "age": raw}).age == 20
    assert User.model_validate({"name": "a", "age": True}).age == 1
    with pytest.raises(ValidationError) as info:
        User.model_validate({"name": "a", "age": 20.5})
    assert info.value.errors()[0]["type"] == "int_from_float"
    with pytest.raises(ValidationError) as info:
        User.model_validate({"name": "a", "age": "1e3"})
    assert info.value.errors()[0]["type"] == "int_parsing"


def test_strict_mode_rejects_conversion() -> None:
    """strict=True / ConfigDict(strict=True) / Field(strict=True) は型変換しない。"""
    with pytest.raises(ValidationError) as info:
        User.model_validate({"name": "a", "age": "20"}, strict=True)
    assert info.value.errors()[0]["type"] == "int_type"
    assert User.model_validate({"name": "a", "age": 20}, strict=True).age == 20

    class StrictModel(BaseModel):
        model_config = ConfigDict(strict=True)
        age: int

    class StrictField(BaseModel):
        age: Annotated[int, Field(strict=True)]
        other: int

    with pytest.raises(ValidationError):
        StrictModel.model_validate({"age": "20"})
    with pytest.raises(ValidationError) as info:
        StrictField.model_validate({"age": "20", "other": "1"})
    assert [e["loc"] for e in info.value.errors()] == [("age",)]


def test_non_dict_input_and_model_instance() -> None:
    """dict でもモデルでもない値は loc () の model_type、同じモデルのインスタンスはそのまま返す。"""
    for raw in (None, [("name", "a")], "{}"):
        with pytest.raises(ValidationError) as info:
            User.model_validate(raw)
        assert info.value.errors()[0]["type"] == "model_type"
        assert info.value.errors()[0]["loc"] == ()
    user = User(name="a", age=1)
    assert User.model_validate(user) is user


def test_defaults_and_missing() -> None:
    """既定値のあるフィールドは補われ、無いフィールドは missing で失敗する。"""
    user = User.model_validate({"name": "a", "age": 1})
    assert user.tags == []
    assert user.addr is None
    with pytest.raises(ValidationError) as info:
        User.model_validate({"name": "a"})
    assert info.value.errors()[0]["type"] == "missing"
    assert info.value.errors()[0]["loc"] == ("age",)


def test_model_dump_and_validate_json() -> None:
    """model_dump は dict に戻し、model_validate_json は JSON 文字列を直接受ける。"""
    user = User.model_validate({"name": "a", "age": 1, "tags": [1], "addr": {"city": "t"}})
    dumped = user.model_dump()
    assert dumped == {"name": "a", "age": 1, "tags": [1], "addr": {"city": "t"}}
    assert isinstance(dumped["addr"], dict)
    assert dumped["tags"] is not user.tags
    assert User.model_validate_json('{"name": "a", "age": "1"}').age == 1
    with pytest.raises(ValidationError) as info:
        User.model_validate_json("{oops")
    assert info.value.errors()[0]["type"] == "json_invalid"


def test_from_attributes_reads_objects() -> None:
    """from_attributes=True で属性を持つ任意のオブジェクトからも読める。"""

    class Row:
        name = "a"
        age = 3

    with pytest.raises(ValidationError):
        User.model_validate(Row())
    assert User.model_validate(Row(), from_attributes=True).age == 3


def test_constructor_with_non_dict_raises_type_error() -> None:
    """Pitfalls: Model(**data) は data が dict でないと TypeError になる。"""
    with pytest.raises(TypeError):
        User(**None)  # type: ignore[arg-type]
