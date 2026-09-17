"""string-case-convert: inflection.underscore / camelize / dasherize / titleize の Contract を検証する。"""

import pytest
from inflection import camelize, dasherize, humanize, titleize, underscore


def test_camel_to_snake() -> None:
    """CamelCase を snake_case にできる。"""
    assert underscore("userProfileURL") == "user_profile_url"
    assert underscore("UserProfileURL") == "user_profile_url"


def test_split_at_lower_or_digit_to_upper_boundary() -> None:
    """小文字または数字→大文字の境界で分割する。"""
    assert underscore("aB") == "a_b"
    assert underscore("version2Update") == "version2_update"


def test_split_consecutive_uppercase_before_last_capitalized_word() -> None:
    """連続大文字は末尾の大文字＋小文字の直前で分割する。"""
    assert underscore("XMLHttpRequest") == "xml_http_request"
    assert underscore("iOS") == "i_os"
    assert underscore("HTTPRequest") == "http_request"


def test_last_uppercase_rule_applies_from_the_end() -> None:
    """連続大文字の末尾規則は末尾側から効く（ABCdef → ab_cdef）。"""
    assert underscore("ABCdef") == "ab_cdef"


def test_hyphen_becomes_underscore() -> None:
    """ハイフンはアンダースコアに置換される。"""
    assert underscore("user-profile-url") == "user_profile_url"


def test_no_split_between_lower_and_digit() -> None:
    """小文字→数字の境界では分割しない（es-toolkit とは違う）。"""
    assert underscore("md5") == "md5"
    assert underscore("utf8") == "utf8"
    assert underscore("html5Parser") == "html5_parser"


def test_spaces_symbols_and_emoji_are_kept() -> None:
    """空白・記号・アポストロフィ・絵文字はそのまま残る。"""
    assert underscore("user profile") == "user profile"
    assert underscore("Don't") == "don't"
    assert underscore("user.profile") == "user.profile"
    assert underscore("hello 🐶 world") == "hello 🐶 world"


def test_non_ascii_is_lowercased_but_not_deburred() -> None:
    """非 ASCII は小文字化されるがアクセントは除去されない。日本語はそのまま。"""
    assert underscore("Crème Brûlée") == "crème brûlée"
    assert underscore("こんにちは 世界") == "こんにちは 世界"


def test_empty_string() -> None:
    """空文字は空文字を返す。"""
    assert underscore("") == ""
    assert camelize("") == ""
    assert dasherize("") == ""
    assert titleize("") == ""


def test_non_str_raises_type_error() -> None:
    """str 以外を渡すと TypeError。"""
    with pytest.raises(TypeError):
        underscore(None)  # type: ignore[arg-type]


def test_camelize_splits_only_on_underscore() -> None:
    """camelize はアンダースコアと先頭だけを区切りにし、大文字境界では分割しない。"""
    assert camelize("user_profile_url") == "UserProfileUrl"
    assert camelize("user_profile_url", False) == "userProfileUrl"
    assert camelize("userProfileURL") == "UserProfileURL"


def test_camelize_lower_first_only_lowercases_first_char() -> None:
    """uppercase_first_letter=False は先頭 1 文字だけを小文字化する。"""
    assert camelize("URLParser", False) == "uRLParser"
    assert camelize(underscore("URLParser"), False) == "urlParser"


def test_camelize_lower_first_on_empty_raises_index_error() -> None:
    """camelize('', False) は IndexError を投げる。"""
    with pytest.raises(IndexError):
        camelize("", False)


def test_dasherize_only_replaces_underscore() -> None:
    """dasherize はアンダースコアをハイフンに置換するだけ。kebab-case は underscore と重ねる。"""
    assert dasherize("user_profile_url") == "user-profile-url"
    assert dasherize("userProfileURL") == "userProfileURL"
    assert dasherize(underscore("XMLHttpRequest")) == "xml-http-request"


def test_titleize_and_humanize() -> None:
    """titleize は各単語の先頭を大文字にし、humanize は先頭だけ大文字にする。"""
    assert titleize("user_profile_url") == "User Profile Url"
    assert titleize("userProfileURL") == "User Profile Url"
    assert humanize("user_profile_url") == "User profile url"


def test_titleize_strips_trailing_id() -> None:
    """titleize / humanize は末尾の _id を落とす。"""
    assert titleize("userID") == "User"
    assert titleize("user_id") == "User"
    assert humanize("author_id") == "Author"
