"""string-slugify: python-slugify の slugify の Contract を検証する。"""

import re

import pytest
from slugify import slugify

ASCII_SLUG = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def test_deburrs_and_kebab_cases() -> None:
    """アクセントを除去し、小文字・ハイフン区切りにする。"""
    assert slugify("Crème Brûlée à la Mode!") == "creme-brulee-a-la-mode"
    assert slugify("Hello, World 2024") == "hello-world-2024"
    assert slugify("naïve café") == "naive-cafe"


def test_separators_do_not_repeat_or_trail() -> None:
    """区切りが連続しても重ならず、先頭・末尾にも付かない。"""
    assert slugify("a--b__c") == "a-b-c"
    assert slugify("  multiple   spaces  ") == "multiple-spaces"
    assert slugify("Hello, World 2024!!") == "hello-world-2024"


def test_latin_extended_letters_are_transliterated() -> None:
    """ラテン拡張文字は ASCII に転写される。"""
    assert slugify("Æther Straße Øre Łódź") == "aether-strasse-ore-lodz"


def test_japanese_and_chinese_are_transliterated_not_removed() -> None:
    """日本語・中国語は除去ではなく転写される（転写結果はバックエンド依存なので ASCII であることと接頭だけを検証）。"""
    ja = slugify("こんにちは 世界")
    assert ASCII_SLUG.match(ja) and ja.startswith("konni") and "-" in ja
    assert slugify("北京") in {"bei-jing", "beijing"}
    assert ASCII_SLUG.match(slugify("Hello こんにちは World"))


def test_emoji_is_removed_and_entities_are_decoded() -> None:
    """絵文字は除去され、HTML エンティティはデコードしてから処理される。"""
    assert slugify("hello 🐶 world") == "hello-world"
    assert slugify("Tom &amp; Jerry") == "tom-jerry"
    assert slugify("&#169; 2024") == "2024"


def test_digits_are_not_split_from_letters() -> None:
    """数字は前後の文字と分割されない。½ は 1-2 になる。"""
    assert slugify("web3") == "web3"
    assert slugify("userProfileURL") == "userprofileurl"
    assert slugify("½ cup") == "1-2-cup"


def test_max_length_cuts_from_the_end() -> None:
    """max_length を超える分は末尾から切り、末尾の区切りは落とす。"""
    assert slugify("Hello World Foo Bar", max_length=8) == "hello-wo"
    assert slugify("Hello World Foo Bar", max_length=6) == "hello"
    assert slugify("Hello World Foo Bar", max_length=12) == "hello-world"


def test_max_length_with_word_boundary_keeps_whole_words() -> None:
    """word_boundary=True なら完全な単語だけを残す。"""
    assert slugify("Hello World Foo Bar", max_length=8, word_boundary=True) == "hello"
    assert slugify("Hello World Foo Bar", max_length=15, word_boundary=True) == "hello-world-foo"


def test_separator_lowercase_and_allow_unicode_options() -> None:
    """separator / lowercase / allow_unicode で出力を変えられる。"""
    assert slugify("Hello World", separator="_") == "hello_world"
    assert slugify("Hello World", lowercase=False) == "Hello-World"
    assert slugify("Crème", allow_unicode=True) == "crème"
    assert slugify("こんにちは 世界", allow_unicode=True) == "こんにちは-世界"


def test_replacements_run_before_transliteration() -> None:
    """replacements で転写前に文字列置換できる。& は既定では消える。"""
    assert slugify("Rock & Roll") == "rock-roll"
    assert slugify("Rock & Roll", replacements=[["&", "and"]]) == "rock-and-roll"


def test_apostrophe_is_a_separator() -> None:
    """アポストロフィは区切りになる。"""
    assert slugify("Don't") == "don-t"


def test_empty_and_symbol_only_input() -> None:
    """空文字・記号のみは空文字を返す。"""
    assert slugify("") == ""
    assert slugify("!!!") == ""


def test_non_string_raises_type_error() -> None:
    """str / bytes / bytearray 以外は TypeError。"""
    with pytest.raises(TypeError):
        slugify(None)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        slugify(123)  # type: ignore[arg-type]


def test_is_pure() -> None:
    """同じ入力からは同じ結果が得られる。"""
    text = "Crème Brûlée"
    assert slugify(text) == slugify(text) == "creme-brulee"
    assert text == "Crème Brûlée"
