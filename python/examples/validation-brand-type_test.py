"""validation-brand-type: typing.NewType の Contract を検証する。"""

import copy
import pickle
from typing import NewType

import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError

UserId = NewType("UserId", str)
OrderId = NewType("OrderId", str)


def test_returns_input_unchanged() -> None:
    """UserId(x) は x をそのまま返し、検査も変換もしない。"""
    raw = "u_1"
    uid = UserId(raw)
    assert uid is raw
    assert type(uid) is str
    assert UserId(3) == 3  # type: ignore[arg-type]
    assert type(UserId(3)) is int  # type: ignore[arg-type]


def test_newtype_object_attributes() -> None:
    """NewType のインスタンスで、__name__ と __supertype__ を持つ。"""
    assert isinstance(UserId, NewType)
    assert UserId.__name__ == "UserId"
    assert UserId.__supertype__ is str
    Nested = NewType("Nested", UserId)
    assert Nested.__supertype__ is UserId


def test_isinstance_and_subclass_raise() -> None:
    """クラスではないので isinstance と継承は TypeError。"""
    with pytest.raises(TypeError):
        isinstance("x", UserId)  # type: ignore[arg-type]
    with pytest.raises(TypeError):

        class Sub(UserId):  # type: ignore[misc,valid-type]
            pass

    assert isinstance(UserId("x"), UserId.__supertype__)


def test_runtime_does_not_distinguish() -> None:
    """実行時は UserId / OrderId / 素の str を区別しない。演算結果は元の型。"""

    def find(user_id: UserId) -> str:
        return user_id

    assert find(UserId("u_1")) == "u_1"
    assert find("u_1") == "u_1"  # type: ignore[arg-type]
    assert find(OrderId("o_1")) == "o_1"  # type: ignore[arg-type]
    assert UserId("u_1") == OrderId("u_1")
    assert type(UserId("a") + "b") is str


def test_pickle_and_copy_keep_value() -> None:
    """pickle / copy は元の値と同じ。"""
    uid = UserId("u_1")
    assert pickle.loads(pickle.dumps(uid)) == "u_1"
    assert copy.deepcopy(uid) == "u_1"


def test_pydantic_treats_newtype_as_supertype() -> None:
    """pydantic は UserId を str として検証し、取り違えも通る。JSON Schema は string。"""

    class Order(BaseModel):
        user_id: UserId
        order_id: OrderId

    order = Order(user_id="o_1", order_id="u_1")  # type: ignore[arg-type]
    assert order.user_id == "o_1"
    assert type(order.user_id) is str
    with pytest.raises(ValidationError) as info:
        Order(user_id=1, order_id="o_1")  # type: ignore[arg-type]
    assert info.value.errors()[0]["type"] == "string_type"
    assert TypeAdapter(UserId).json_schema() == {"type": "string"}


def test_str_subclass_alternative_is_distinguishable() -> None:
    """Alternatives: str のサブクラスなら isinstance が使えるが、演算結果は str に戻る。"""

    class StrictUserId(str):
        pass

    uid = StrictUserId("u_1")
    assert isinstance(uid, StrictUserId)
    assert not isinstance("u_1", StrictUserId)
    assert type(uid.upper()) is str
