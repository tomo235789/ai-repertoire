# カード collection-dedup-by-key の Contract を検証するテスト
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


DATA = "WITH t(id, name, ts) AS (VALUES (1, 'a', 3), (2, 'b', 1), (1, 'c', 2))"
DEDUP = (
    DATA
    + " SELECT id, name FROM (SELECT id, name, ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts) AS rn FROM t)"
    " WHERE rn = 1 ORDER BY id"
)


@pytest.mark.parametrize("engine", ENGINES)
def test_keeps_one_row_per_key_chosen_by_order_by(engine):
    """キーごとに 1 行、OVER の ORDER BY で最小の ts を持つ行が残る"""
    assert run(engine, DEDUP) == [(1, "c"), (2, "b")]


@pytest.mark.parametrize("engine", ENGINES)
def test_desc_keeps_the_last_row(engine):
    """ORDER BY ts DESC なら ts が最大の行が残る"""
    sql = DEDUP.replace("ORDER BY ts", "ORDER BY ts DESC")
    assert run(engine, sql) == [(1, "a"), (2, "b")]


@pytest.mark.parametrize("engine", ENGINES)
def test_without_order_by_still_one_row_per_key_but_which_is_unspecified(engine):
    """OVER の ORDER BY を省いてもキーごとに 1 行にはなるが、どの行かは不定（件数だけ検証）"""
    sql = DEDUP.replace(" ORDER BY ts", "")
    rows = run(engine, sql)
    assert [r[0] for r in rows] == [1, 2]
    assert rows[0][1] in ("a", "c")


@pytest.mark.parametrize("engine", ENGINES)
def test_null_keys_form_one_group(engine):
    """NULL のキーは同じグループになり 1 行残る"""
    sql = (
        "WITH t(id, name, ts) AS (VALUES (1, 'a', 3), (NULL, 'd', 5), (NULL, 'e', 0))"
        " SELECT id, name FROM (SELECT id, name, ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts) AS rn FROM t)"
        " WHERE rn = 1 ORDER BY id NULLS FIRST"
    )
    assert run(engine, sql) == [(None, "e"), (1, "a")]


@pytest.mark.parametrize("engine", ENGINES)
def test_row_number_is_dense_from_one(engine):
    """rn はキーごとに 1 から順に振られる（rn <= n で上位 n 件）"""
    sql = (
        DATA
        + " SELECT id, name, rn FROM (SELECT id, name, ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts) AS rn FROM t)"
        " ORDER BY id, rn"
    )
    assert run(engine, sql) == [(1, "c", 1), (1, "a", 2), (2, "b", 1)]


@pytest.mark.parametrize("engine", ENGINES)
def test_empty_input_returns_no_rows(engine):
    """0 行なら 0 行"""
    sql = DEDUP.replace(
        "VALUES (1, 'a', 3), (2, 'b', 1), (1, 'c', 2)", "SELECT 1, 'a', 3 WHERE 0"
    )
    assert run(engine, sql) == []


@pytest.mark.parametrize("engine", ENGINES)
def test_window_function_not_allowed_in_where(engine):
    """WHERE に窓関数を直接書くとエラー"""
    sql = (
        DATA
        + " SELECT id, name FROM t WHERE ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts) = 1"
    )
    with pytest.raises(Exception):
        run(engine, sql)


def test_duckdb_qualify_and_distinct_on():
    """Alternatives: duckdb は QUALIFY と DISTINCT ON で 1 段で書ける。sqlite は構文エラー"""
    qualify = (
        DATA
        + " SELECT id, name FROM t QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts) = 1 ORDER BY id"
    )
    distinct_on = DATA + " SELECT DISTINCT ON (id) id, name FROM t ORDER BY id, ts"
    assert run("duckdb", qualify) == [(1, "c"), (2, "b")]
    assert run("duckdb", distinct_on) == [(1, "c"), (2, "b")]
    with pytest.raises(sqlite3.OperationalError):
        run("sqlite", qualify)
    with pytest.raises(sqlite3.OperationalError):
        run("sqlite", distinct_on)


TIES_AND_NULLS = "WITH t(id, name, ts) AS (VALUES (1, 'a', 3), (2, 'b', 1), (1, 'c', 2), (NULL, 'd', 5), (NULL, 'e', 0), (3, 'x', 7), (3, 'y', 7))"


@pytest.mark.parametrize("engine", ENGINES)
def test_not_exists_alternative_needs_null_safe_equality_and_tie_breaker(engine):
    """Alternatives: NOT EXISTS 版は NULL 安全な比較と一意なタイブレークを足して初めて ROW_NUMBER 版と一致する（name を一意列として使う）"""
    null_safe = "IS" if engine == "sqlite" else "IS NOT DISTINCT FROM"
    reference = (
        TIES_AND_NULLS
        + " SELECT id, name FROM (SELECT id, name, ROW_NUMBER() OVER (PARTITION BY id ORDER BY ts, name) AS rn FROM t)"
        " WHERE rn = 1 ORDER BY id NULLS FIRST, name"
    )
    naive = (
        TIES_AND_NULLS
        + " SELECT id, name FROM t WHERE NOT EXISTS (SELECT 1 FROM t AS u WHERE u.id = t.id AND u.ts < t.ts)"
        " ORDER BY id NULLS FIRST, name"
    )
    fixed = (
        TIES_AND_NULLS
        + f" SELECT id, name FROM t WHERE NOT EXISTS (SELECT 1 FROM t AS u WHERE u.id {null_safe} t.id"
        " AND (u.ts < t.ts OR (u.ts = t.ts AND u.name < t.name))) ORDER BY id NULLS FIRST, name"
    )
    expected = [(None, "e"), (1, "c"), (2, "b"), (3, "x")]
    assert run(engine, reference) == expected
    assert run(engine, naive) == [
        (None, "d"),
        (None, "e"),
        (1, "c"),
        (2, "b"),
        (3, "x"),
        (3, "y"),
    ]
    assert run(engine, fixed) == expected


def test_group_by_with_bare_column_is_sqlite_only():
    """Pitfalls: GROUP BY + MIN + 裸の列は sqlite では MIN の行の値が入るが、duckdb はエラー"""
    sql = DATA + " SELECT id, MIN(ts), name FROM t GROUP BY id ORDER BY id"
    assert run("sqlite", sql) == [(1, 2, "c"), (2, 1, "b")]
    with pytest.raises(duckdb.BinderException):
        run("duckdb", sql)
