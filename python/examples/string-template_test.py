"""string-template: string.Template の Contract を検証する。"""

import os
from string import Template

import pytest

T = Template("Hello, $name! You have ${count} items. Cost: $$5")


def test_substitute_with_kwargs_mapping_and_priority() -> None:
    """$name / ${name} / $$ を置換する。マッピングとキーワードを併用でき、同じキーはキーワードが優先。"""
    assert T.substitute(name="Ann", count=3) == "Hello, Ann! You have 3 items. Cost: $5"
    assert T.substitute({"name": "Ann", "count": 3}) == "Hello, Ann! You have 3 items. Cost: $5"
    assert T.substitute({"name": "A", "count": 1}, name="B") == "Hello, B! You have 1 items. Cost: $5"


def test_missing_key_raises_key_error_and_safe_substitute_keeps_placeholder() -> None:
    """substitute は足りないキーで KeyError、safe_substitute はプレースホルダーをそのまま残す。"""
    with pytest.raises(KeyError) as info:
        T.substitute(name="Ann")
    assert info.value.args == ("count",)
    assert T.safe_substitute(name="Ann") == "Hello, Ann! You have ${count} items. Cost: $5"


def test_invalid_placeholder() -> None:
    """$1 や末尾の $ は substitute で ValueError、safe_substitute では残る。is_valid で事前に確認できる。"""
    for text in ("$1", "price: $"):
        with pytest.raises(ValueError, match="Invalid placeholder in string"):
            Template(text).substitute()
        assert Template(text).safe_substitute() == text
        assert Template(text).is_valid() is False
    assert T.is_valid() is True


def test_identifier_rules() -> None:
    """識別子は [_a-zA-Z][_a-zA-Z0-9]* で、$name_x は 1 語。${name}_x で区切る。"""
    assert Template("$name_x").safe_substitute(name="cat") == "$name_x"
    assert Template("${name}_x $names ${name}s").substitute(name="cat", names="N") == "cat_x N cats"
    assert T.get_identifiers() == ["name", "count"]
    assert T.template == "Hello, $name! You have ${count} items. Cost: $$5"


def test_values_are_converted_with_str() -> None:
    """値は str() で文字列化される。書式指定は無い。"""
    assert Template("$v").substitute(v=None) == "None"
    assert Template("$v").substitute(v=1.5) == "1.5"
    assert Template("$v").substitute(v=[1, "a"]) == "[1, 'a']"


def test_any_mapping_is_accepted(monkeypatch: pytest.MonkeyPatch) -> None:
    """第 1 引数は os.environ など任意のマッピング（ホストの環境変数には依存しない）。"""
    monkeypatch.setenv("AI_REPERTOIRE_TEMPLATE_TEST", "ok")
    assert Template("$AI_REPERTOIRE_TEMPLATE_TEST").substitute(os.environ) == "ok"


def test_no_attribute_access_unlike_str_format() -> None:
    """$s.password は $s だけ置換され属性アクセスは起きない。str.format の {s.password} は属性を読む。"""

    class Config:
        password = "hunter2"

    assert Template("$s.password").substitute(s="S") == "S.password"
    assert "{s.password}".format(s=Config()) == "hunter2"


def test_braces_are_literal_and_dollar_needs_escaping() -> None:
    """Pitfalls: { } は文字のままで、$ は $$ にする。"""
    assert Template('{"total": $v}').substitute(v=1) == '{"total": 1}'
    assert Template("$$$v").substitute(v=5) == "$5"


def test_custom_delimiter() -> None:
    """Alternatives: delimiter を差し替えられる。"""

    class PercentTemplate(Template):
        delimiter = "%"

    assert PercentTemplate("%name %% $x").substitute(name="a") == "a % $x"
