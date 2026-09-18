"""validation-email: EmailStr の Contract を検証する。"""

import pytest
from pydantic import BaseModel, EmailStr, NameEmail, TypeAdapter, ValidationError, validate_email

Email = TypeAdapter(EmailStr)


def error(value: object) -> dict:
    """失敗の最初の errors() 要素を返す。"""
    with pytest.raises(ValidationError) as info:
        Email.validate_python(value)
    return info.value.errors(include_url=False)[0]


def test_valid_addresses_pass_as_str() -> None:
    """通る例は str のまま返る。"""
    for value in (
        "user@example.com",
        "first.last+tag@example.co.jp",
        "a@b.c",
        "user@sub.example.com",
        "ユーザー@example.com",
        "user@例え.jp",
    ):
        result = Email.validate_python(value)
        assert result == value
        assert type(result) is str


def test_invalid_addresses_fail() -> None:
    """通らない例は value_error、文字列以外は string_type。"""
    for value in (
        "user@localhost",
        "user@example",
        "user@127.0.0.1",
        "user@[192.168.0.1]",
        '"quoted"@example.com',
        ".user@example.com",
        "user..dot@example.com",
        "user@exa_mple.com",
        "user@example-.com",
        "user name@example.com",
        "",
    ):
        err = error(value)
        assert err["type"] == "value_error", value
        assert err["msg"].startswith("value is not a valid email address: ")
    assert error("user@localhost")["msg"].endswith("It should have a period.")
    assert error(123)["type"] == "string_type"
    assert error(None)["type"] == "string_type"


def test_normalization() -> None:
    """ドメインは小文字化、ローカル部はそのまま、前後の空白は除去、Punycode は Unicode に戻る。"""
    assert Email.validate_python("User@Example.COM") == "User@example.com"
    assert Email.validate_python("USER@example.com") == "USER@example.com"
    assert Email.validate_python(" user@example.com \n") == "user@example.com"
    assert Email.validate_python("user@xn--r8jz45g.jp") == "user@例え.jp"


def test_no_deliverability_check() -> None:
    """DNS 引きはせず、存在しないドメインも通る。"""
    assert Email.validate_python("user@thisdomaindoesnotexist.example") == "user@thisdomaindoesnotexist.example"


def test_strict_mode_still_normalizes() -> None:
    """strict=True でも同じ検証・正規化が走る。"""
    assert Email.validate_python("User@Example.COM", strict=True) == "User@example.com"
    with pytest.raises(ValidationError):
        Email.validate_python("user@localhost", strict=True)


def test_in_model_and_dump() -> None:
    """モデルのフィールドとして使うと正規化された str が入り、dump も str。"""

    class Signup(BaseModel):
        email: EmailStr

    signup = Signup(email="User@Example.COM")
    assert signup.email == "User@example.com"
    assert signup.model_dump() == {"email": "User@example.com"}
    assert signup.model_dump_json() == '{"email":"User@example.com"}'


def test_name_email() -> None:
    """NameEmail は name / email に分け、str() で 'Name <email>' に戻る。"""
    parsed = TypeAdapter(NameEmail).validate_python("Alice Smith <Alice@Example.COM>")
    assert parsed.name == "Alice Smith"
    assert parsed.email == "Alice@example.com"
    assert str(parsed) == "Alice Smith <Alice@example.com>"
    assert parsed == NameEmail("Alice Smith", "Alice@example.com")
    bare = TypeAdapter(NameEmail).validate_python("alice@example.com")
    assert (bare.name, bare.email) == ("alice", "alice@example.com")

    class Mail(BaseModel):
        to: NameEmail

    assert Mail(to="Alice <alice@example.com>").model_dump_json() == '{"to":"Alice <alice@example.com>"}'


def test_validate_email_function() -> None:
    """validate_email 関数は (name, normalized_email) を返す。"""
    assert validate_email("Alice <Alice@Example.COM>") == ("Alice", "Alice@example.com")
    assert validate_email("alice@example.com") == ("alice", "alice@example.com")


def test_email_str_cannot_be_instantiated() -> None:
    """EmailStr は検証用の型で、str のサブクラスではない。"""
    assert not issubclass(EmailStr, str)
