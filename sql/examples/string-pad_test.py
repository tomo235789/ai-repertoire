# カード string-pad の Contract を検証するテスト
import sqlite3

import duckdb
import pytest


def run(engine, sql):
    """sqlite / duckdb のどちらかで SQL を実行して全行を返す"""
    if engine == "sqlite":
        con = sqlite3.connect(":memory:")
    else:
        con = duckdb.connect()
    try:
        return con.execute(sql).fetchall()
    finally:
        con.close()


def test_lpad_rpad_basic():
    """左右にそれぞれ埋めて指定幅にする"""
    assert run(
        "duckdb",
        "SELECT LPAD('42', 5, '0'), RPAD('42', 5, '0'), LPAD('abc', 5, ' '), LPAD('', 3, 'x')",
    ) == [("00042", "42000", "  abc", "xxx")]


def test_longer_input_is_truncated_to_head():
    """幅を超えると先頭 n 文字に切り詰める（LPAD / RPAD とも）"""
    sql = "SELECT LPAD('abcdefg', 5, '0'), RPAD('abcdefg', 5, '0'), LPAD('abc', 1, 'x'), RPAD('abc', 1, 'x')"
    assert run("duckdb", sql) == [("abcde", "abcde", "a", "a")]


def test_zero_or_negative_width_and_exact_width():
    """n <= 0 なら空文字、n = LENGTH(s) ならそのまま"""
    assert run(
        "duckdb", "SELECT LPAD('ab', 0, 'x'), LPAD('ab', -1, 'x'), LPAD('ab', 2, 'x')"
    ) == [("", "", "ab")]


def test_multi_char_fill_is_repeated_and_cut_from_head():
    """複数文字の fill は繰り返し、端数は先頭から切る"""
    assert run(
        "duckdb", "SELECT LPAD('ab', 5, 'xy'), LPAD('ab', 6, 'xy'), RPAD('ab', 5, 'xy')"
    ) == [("xyxab", "xyxyab", "abxyx")]


def test_empty_fill_errors_only_when_padding_needed():
    """fill が空だと埋めが必要なときだけエラー"""
    with pytest.raises(duckdb.InvalidInputException):
        run("duckdb", "SELECT LPAD('ab', 5, '')")
    assert run("duckdb", "SELECT LPAD('ab', 2, '')") == [("ab",)]


def test_length_is_in_code_points():
    """長さはコードポイント。結合文字は 2 と数える"""
    sql = "SELECT LPAD('あ', 3, '*'), LPAD('😀', 3, '*'), LPAD('e' || chr(769), 3, '*'), LENGTH('e' || chr(769))"
    assert run("duckdb", sql) == [("**あ", "**😀", "*é", 2)]


def test_null_propagates():
    """どの引数も NULL なら NULL"""
    assert run(
        "duckdb",
        "SELECT LPAD(NULL, 5, '0'), LPAD('ab', NULL, 'x'), LPAD('ab', 5, NULL)",
    ) == [(None, None, None)]


def test_first_argument_must_be_string():
    """整数を渡すと Binder Error。VARCHAR にキャストすれば通る"""
    with pytest.raises(duckdb.BinderException):
        run("duckdb", "SELECT LPAD(42, 5, '0')")
    assert run(
        "duckdb", "SELECT LPAD(42::VARCHAR, 5, '0'), typeof(LPAD('42', 5, '0'))"
    ) == [("00042", "VARCHAR")]


def test_sqlite_has_no_lpad_and_uses_printf_or_substr():
    """Alternatives: sqlite に LPAD は無い。printf は切り詰めず、SUBSTR は末尾が残る"""
    with pytest.raises(sqlite3.OperationalError):
        run("sqlite", "SELECT LPAD('42', 5, '0')")
    sql = (
        "SELECT printf('%05d', 42), printf('%05d', -42), printf('%05d', 123456), printf('%-5s|', 'ab'),"
        " SUBSTR('00000' || '42', -5), SUBSTR('00000' || 'abcdefg', -5), printf('%5s|', 'あい')"
    )
    assert run("sqlite", sql) == [
        ("00042", "-0042", "123456", "ab   |", "00042", "cdefg", "あい|")
    ]


def test_centering_requires_integer_width():
    """Alternatives: センタリングは幅を INTEGER に CAST する。LENGTH は BIGINT、/ は DOUBLE で、そのままだと Binder Error"""
    center = "LPAD(RPAD(s, CAST((LENGTH(s) + 8) // 2 AS INTEGER), ' '), 8, ' ')"
    sql = f"WITH t(s) AS (VALUES ('abc'), ('ab'), ('abcdefghij')) SELECT '[' || {center} || ']' FROM t"
    assert run("duckdb", sql) == [("[   abc  ]",), ("[   ab   ]",), ("[abcdefgh]",)]
    for width in ["(LENGTH(s) + 8) / 2", "(LENGTH(s) + 8) // 2", "LENGTH(s) + 2"]:
        with pytest.raises(duckdb.BinderException):
            run(
                "duckdb",
                f"WITH t(s) AS (VALUES ('abc')) SELECT RPAD(s, {width}, ' ') FROM t",
            )


def test_duckdb_format_and_printf_alternatives():
    """Alternatives: duckdb の format / printf でもゼロ埋めできる"""
    assert run("duckdb", "SELECT format('{:05d}', 42), printf('%05d', 42)") == [
        ("00042", "00042")
    ]
