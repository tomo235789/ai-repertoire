# カード number-clamp の Contract を検証するテスト
import math
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


DATA = "WITH t(v) AS (VALUES (120), (-5), (42), (NULL))"


def test_sqlite_scalar_min_max_clamps_per_row():
    """sqlite: 2 引数以上の MIN / MAX はスカラー。範囲外は境界値、境界値は含む"""
    sql = DATA + " SELECT v, MIN(MAX(v, 0), 100) FROM t ORDER BY v"
    assert run("sqlite", sql) == [(None, None), (-5, 0), (42, 42), (120, 100)]
    assert run("sqlite", "SELECT MIN(MAX(0, 0), 100), MIN(MAX(100, 0), 100)") == [
        (0, 100)
    ]


def test_sqlite_one_argument_is_aggregate():
    """sqlite: 1 引数の MAX は集計（1 行）、2 引数は行ごと"""
    assert run(
        "sqlite", "WITH t(v) AS (VALUES (1), (2), (3)) SELECT MAX(v) FROM t"
    ) == [(3,)]
    assert run(
        "sqlite", "WITH t(v) AS (VALUES (1), (2), (3)) SELECT MIN(v, 2) FROM t"
    ) == [(1,), (2,), (2,)]


def test_lo_greater_than_hi_returns_hi_for_non_null_x():
    """lo > hi なら x が非 NULL のとき hi。x が NULL なら sqlite は NULL、duckdb は NULL を無視して hi"""
    assert run(
        "sqlite",
        "SELECT MIN(MAX(50, 100), 0), MIN(MAX(0, 100), 0), MIN(MAX(NULL, 100), 0)",
    ) == [(0, 0, None)]
    assert run(
        "duckdb",
        "SELECT LEAST(GREATEST(50, 100), 0), LEAST(GREATEST(0, 100), 0), LEAST(GREATEST(NULL, 100), 0)",
    ) == [(0, 0, 0)]


def test_null_propagates_in_sqlite_but_is_ignored_in_duckdb():
    """NULL: sqlite は NULL を返し、duckdb の LEAST/GREATEST は NULL を無視する"""
    assert run(
        "sqlite", "SELECT MAX(NULL, 0), MIN(NULL, 100), MIN(MAX(NULL, 0), 100)"
    ) == [(None, None, None)]
    assert run(
        "duckdb",
        "SELECT GREATEST(NULL, 0), LEAST(NULL, 100), LEAST(GREATEST(NULL, 0), 100), GREATEST(NULL, NULL)",
    ) == [(0, 100, 0, None)]
    rows = run(
        "duckdb",
        DATA + " SELECT v, LEAST(GREATEST(v, 0), 100) FROM t ORDER BY v NULLS FIRST",
    )
    assert rows == [(None, 0), (-5, 0), (42, 42), (120, 100)]


def test_sqlite_returns_chosen_value_with_its_type():
    """sqlite: 返り値は選ばれた引数の値と型そのまま"""
    sql = "SELECT MIN(MAX(5, 0), 100), typeof(MIN(MAX(5, 0), 100)), MIN(MAX(1.5, 0), 100), typeof(MIN(MAX(1.5, 0), 100))"
    assert run("sqlite", sql) == [(5, "integer", 1.5, "real")]


def test_sqlite_mixed_types_compare_by_type_order():
    """sqlite: TEXT は数値より大きいので文字列を渡すと壊れる"""
    assert run("sqlite", "SELECT MAX('5', 0), MIN(MAX('5', 0), 100)") == [("5", 100)]


def test_duckdb_nested_min_max_is_an_error():
    """duckdb: MAX(x, n) は上位 n 件の集計で、入れ子は Binder Error"""
    with pytest.raises(duckdb.BinderException):
        run("duckdb", "SELECT MIN(MAX(120, 0), 100)")
    assert run("duckdb", "SELECT typeof(MAX(120, 0))") == [("INTEGER[]",)]


def test_duckdb_nan_is_treated_as_maximum():
    """duckdb: NaN は最大値扱いなので clamp の結果は hi"""
    rows = run(
        "duckdb",
        "SELECT GREATEST('nan'::DOUBLE, 0), LEAST(GREATEST('nan'::DOUBLE, 0), 100)",
    )
    assert math.isnan(rows[0][0])
    assert rows[0][1] == 100.0


def test_sqlite_has_no_least_greatest():
    """sqlite に LEAST / GREATEST は無い"""
    with pytest.raises(sqlite3.OperationalError):
        run("sqlite", "SELECT LEAST(GREATEST(120, 0), 100)")


@pytest.mark.parametrize("engine", ENGINES)
def test_case_expression_is_portable(engine):
    """Alternatives: CASE 式はどちらでも同じ結果で NULL は NULL のまま"""
    sql = (
        DATA
        + " SELECT v, CASE WHEN v < 0 THEN 0 WHEN v > 100 THEN 100 ELSE v END FROM t ORDER BY v NULLS FIRST"
    )
    assert run(engine, sql) == [(None, None), (-5, 0), (42, 42), (120, 100)]
