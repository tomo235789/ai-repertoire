"""http-fetch-json-typed: raise_for_status + model_validate_json の Contract を検証する。"""

import json

import httpx
import pytest
from pydantic import BaseModel, TypeAdapter, ValidationError


class User(BaseModel):
    id: int
    name: str


def handler(request: httpx.Request) -> httpx.Response:
    path = request.url.path
    if path == "/ok":
        return httpx.Response(200, json={"id": 1, "name": "ann", "extra": True})
    if path == "/html":
        return httpx.Response(200, headers={"Content-Type": "application/json"}, text="<html>login</html>")
    if path == "/text-plain":
        return httpx.Response(200, headers={"Content-Type": "text/plain"}, text='{"id": 2, "name": "bob"}')
    if path == "/wrong-shape":
        return httpx.Response(200, json={"id": "x"})
    if path == "/string-id":
        return httpx.Response(200, json={"id": "1", "name": "ann"})
    if path == "/list":
        return httpx.Response(200, json=[{"id": 1, "name": "a"}, {"id": 2, "name": "b"}])
    if path == "/error":
        return httpx.Response(500, json={"error": "boom"})
    if path == "/no-content":
        return httpx.Response(204)
    return httpx.Response(404)


@pytest.fixture
def client() -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def fetch_user(client: httpx.Client, path: str) -> User:
    """カードの Usage と同じ形。"""
    r = client.get(f"https://example.com{path}").raise_for_status()
    return User.model_validate_json(r.content)


def test_returns_typed_model_and_ignores_unknown_keys(client: httpx.Client) -> None:
    """成功すると Model のインスタンス。未知のキーは無視される。"""
    user = fetch_user(client, "/ok")
    assert isinstance(user, User)
    assert user == User(id=1, name="ann")
    assert user.model_dump() == {"id": 1, "name": "ann"}


def test_raise_for_status_returns_response_or_raises(client: httpx.Client) -> None:
    """raise_for_status() は 2xx なら Response 自身を返し、4xx / 5xx なら HTTPStatusError。"""
    response = client.get("https://example.com/ok")
    assert response.raise_for_status() is response
    with pytest.raises(httpx.HTTPStatusError) as info:
        fetch_user(client, "/error")
    assert info.value.response.status_code == 500
    assert not isinstance(info.value, ValueError)


def test_accepts_bytes_str_and_bytearray(client: httpx.Client) -> None:
    """bytes / str / bytearray のどれでも受け取る。"""
    response = client.get("https://example.com/ok")
    assert isinstance(response.content, bytes)
    assert User.model_validate_json(response.content) == User.model_validate_json(response.text)
    assert User.model_validate_json(bytearray(response.content)) == User(id=1, name="ann")


@pytest.mark.parametrize("path", ["/html", "/no-content"])
def test_non_json_body_is_validation_error(client: httpx.Client, path: str) -> None:
    """本文が JSON でなければ ValidationError で、type は json_invalid。ValueError のサブクラス。"""
    with pytest.raises(ValidationError) as info:
        fetch_user(client, path)
    assert isinstance(info.value, ValueError)
    assert info.value.errors()[0]["type"] == "json_invalid"
    assert info.value.errors()[0]["loc"] == ()


def test_wrong_shape_reports_all_fields(client: httpx.Client) -> None:
    """フィールドの不一致は loc 付きで全フィールド分まとめて報告される。"""
    with pytest.raises(ValidationError) as info:
        fetch_user(client, "/wrong-shape")
    assert [(e["loc"], e["type"]) for e in info.value.errors()] == [(("id",), "int_parsing"), (("name",), "missing")]


def test_content_type_is_ignored(client: httpx.Client) -> None:
    """Content-Type は見ない。text/plain でも本文が JSON なら成功する。"""
    assert fetch_user(client, "/text-plain") == User(id=2, name="bob")


def test_lax_coercion_and_strict(client: httpx.Client) -> None:
    """既定では "1" が int に変換され、strict=True なら ValidationError。"""
    content = client.get("https://example.com/string-id").content
    assert User.model_validate_json(content).id == 1
    with pytest.raises(ValidationError) as info:
        User.model_validate_json(content, strict=True)
    assert info.value.errors()[0]["type"] == "int_type"


def test_type_adapter_for_top_level_list(client: httpx.Client) -> None:
    """Alternatives: トップレベルが配列なら TypeAdapter(list[Model]).validate_json。"""
    users = TypeAdapter(list[User]).validate_json(client.get("https://example.com/list").content)
    assert users == [User(id=1, name="a"), User(id=2, name="b")]


def test_response_json_raises_json_decode_error_for_html(client: httpx.Client) -> None:
    """Pitfalls: r.json() 経由だと非 JSON は json.JSONDecodeError になり、例外の種類が 2 つに分かれる。"""
    response = client.get("https://example.com/html")
    with pytest.raises(json.JSONDecodeError):
        response.json()
    with pytest.raises(ValidationError):
        User.model_validate_json(response.content)
