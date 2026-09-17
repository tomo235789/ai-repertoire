# カード string-truncate の Contract を検証するテスト
import sqlite3

import duckdb
import pytest

ENGINES = ["sqlite", "duckdb"]


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


TRUNC5 = "CASE WHEN LENGTH(s) > 5 THEN SUBSTR(s, 1, 5) || '...' ELSE s END"


@pytest.mark.parametrize("engine", ENGINES)
def test_truncates_only_when_longer_than_n(engine):
    """n を超えるときだけ先頭 n 文字 + '...'。ちょうど n 文字はそのまま。NULL は NULL"""
    sql = f"WITH t(pos, s) AS (VALUES (1, 'hello world'), (2, 'hi'), (3, 'abcde'), (4, NULL)) SELECT {TRUNC5} FROM t ORDER BY pos"
    assert run(engine, sql) == [("hello...",), ("hi",), ("abcde",), (None,)]


@pytest.mark.parametrize("engine", ENGINES)
def test_length_and_substr_count_code_points(engine):
    """LENGTH / SUBSTR はコードポイント単位。結合文字は 2"""
    sql = f"WITH t(pos, s) AS (VALUES (1, 'こんにちは世界'), (2, '😀😀😀😀😀😀')) SELECT {TRUNC5}, LENGTH(s) FROM t ORDER BY pos"
    assert run(engine, sql) == [("こんにちは...", 7), ("😀😀😀😀😀...", 6)]
    chr_fn = "char" if engine == "sqlite" else "chr"
    assert run(engine, f"SELECT LENGTH('e' || {chr_fn}(769))") == [(2,)]


@pytest.mark.parametrize("engine", ENGINES)
def test_fit_within_n_including_ellipsis(engine):
    """省略記号込みで n 文字に収めるなら SUBSTR(s, 1, n - 3)"""
    sql = "WITH t(pos, s) AS (VALUES (1, 'hello world'), (2, 'abcdefgh')) SELECT CASE WHEN LENGTH(s) > 8 THEN SUBSTR(s, 1, 8 - 3) || '...' ELSE s END FROM t ORDER BY pos"
    assert run(engine, sql) == [("hello...",), ("abcdefgh",)]


@pytest.mark.parametrize("engine", ENGINES)
def test_substr_start_index_semantics(engine):
    """SUBSTR は 1 始まり。0 は 1 文字前から数えて 1 文字少ない。負は末尾から"""
    sql = "SELECT SUBSTR('hello', 1, 3), SUBSTR('hello', 0, 3), SUBSTR('hello', -3), SUBSTR('hello', 2)"
    assert run(engine, sql) == [("hel", "he", "llo", "ello")]


@pytest.mark.parametrize("engine", ENGINES)
def test_substr_length_edge_cases(engine):
    """len が長すぎても全体、0 なら空文字。負なら start の手前を返す（1 文字目の手前は空）"""
    sql = "SELECT SUBSTR('hello', 1, 100), SUBSTR('hello', 1, 0), SUBSTR('hello', 1, -1), SUBSTR('hello', 3, -2), SUBSTR('hello', 4, -3), SUBSTR('', 1, 3), SUBSTR(NULL, 1, 3)"
    assert run(engine, sql) == [("hello", "", "", "he", "hel", "", None)]


@pytest.mark.parametrize("engine", ENGINES)
def test_unicode_ellipsis_is_one_char(engine):
    """'…' は 1 文字"""
    sql = "WITH t(s) AS (VALUES ('hello world')) SELECT CASE WHEN LENGTH(s) > 5 THEN SUBSTR(s, 1, 5) || '…' ELSE s END, LENGTH('…') FROM t"
    assert run(engine, sql) == [("hello…", 1)]


def test_numeric_argument_handling_differs():
    """sqlite は数値を文字列扱い、duckdb は Binder Error"""
    assert run("sqlite", "SELECT SUBSTR(12345, 1, 2), LENGTH(123)") == [("12", 3)]
    with pytest.raises(duckdb.BinderException):
        run("duckdb", "SELECT SUBSTR(12345, 1, 2)")


def test_left_exists_in_duckdb_not_sqlite():
    """Alternatives: LEFT は duckdb にあり sqlite に無い。SUBSTRING は両方"""
    assert run(
        "duckdb", "SELECT LEFT('hello world', 5), LEFT('hi', 5), LEFT('hello', -1)"
    ) == [("hello", "hi", "hell")]
    with pytest.raises(sqlite3.OperationalError):
        run("sqlite", "SELECT LEFT('hello', 3)")
    for engine in ENGINES:
        assert run(engine, "SELECT SUBSTRING('hello', 1, 3)") == [("hel",)]


def test_byte_length_alternatives():
    """Alternatives: バイト数は sqlite が LENGTH(CAST AS BLOB)、duckdb が STRLEN"""
    assert run(
        "sqlite", "SELECT LENGTH(CAST('こんにちは' AS BLOB)), LENGTH('こんにちは')"
    ) == [(15, 5)]
    assert run("duckdb", "SELECT STRLEN('こんにちは'), LENGTH('こんにちは')") == [
        (15, 5)
    ]


def test_sqlite_length_stops_at_nul():
    """Pitfalls: sqlite の LENGTH は NUL 文字まで"""
    assert run("sqlite", "SELECT LENGTH('a' || char(0) || 'b')") == [(1,)]
