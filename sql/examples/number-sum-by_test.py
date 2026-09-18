# カード number-sum-by の Contract を検証するテスト
import sqlite3
from decimal import Decimal

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


DATA = "WITH t(qty) AS (VALUES (1), (2), (NULL), (3))"


@pytest.mark.parametrize("engine", ENGINES)
def test_null_values_are_ignored(engine):
    """NULL は無視して合計する"""
    assert run(engine, DATA + " SELECT SUM(qty), COUNT(qty), COUNT(*) FROM t") == [
        (6, 3, 4)
    ]


@pytest.mark.parametrize("engine", ENGINES)
def test_no_rows_or_all_null_gives_null_not_zero(engine):
    """該当 0 行・全部 NULL なら NULL。COALESCE で 0 にする"""
    assert run(
        engine, DATA + " SELECT SUM(qty), COALESCE(SUM(qty), 0) FROM t WHERE qty > 100"
    ) == [(None, 0)]
    assert run(
        engine,
        "WITH t(qty) AS (VALUES (NULL), (NULL)) SELECT SUM(qty), COALESCE(SUM(qty), 0) FROM t",
    ) == [(None, 0)]


def test_sqlite_total_returns_real_and_zero_for_empty():
    """sqlite の TOTAL は常に REAL で、空なら 0.0。duckdb には無い"""
    sql = "WITH t(v) AS (SELECT 1 WHERE 0) SELECT SUM(v), TOTAL(v), typeof(TOTAL(v)) FROM t"
    assert run("sqlite", sql) == [(None, 0.0, "real")]
    assert run(
        "sqlite",
        "WITH t(v) AS (VALUES (1), (2)) SELECT TOTAL(v), typeof(TOTAL(v)) FROM t",
    ) == [(3.0, "real")]
    with pytest.raises(duckdb.CatalogException):
        run("duckdb", "WITH t(v) AS (VALUES (1), (2)) SELECT TOTAL(v) FROM t")


def test_result_type_by_dialect():
    """sqlite は INTEGER / REAL、duckdb は HUGEINT / DECIMAL / DOUBLE"""
    ints = "WITH t(v) AS (VALUES (1), (2), (3)) SELECT SUM(v), typeof(SUM(v)) FROM t"
    assert run("sqlite", ints) == [(6, "integer")]
    assert run("duckdb", ints) == [(6, "HUGEINT")]
    mixed = "WITH t(v) AS (VALUES (1), (2.5)) SELECT SUM(v), typeof(SUM(v)) FROM t"
    assert run("sqlite", mixed) == [(3.5, "real")]
    assert run("duckdb", mixed) == [(Decimal("3.5"), "DECIMAL(38,1)")]
    assert run(
        "duckdb",
        "WITH t(v) AS (VALUES (1.5::DOUBLE), (2.5::DOUBLE)) SELECT SUM(v), typeof(SUM(v)) FROM t",
    ) == [(4.0, "DOUBLE")]


def test_integer_overflow_behavior():
    """sqlite は 64 ビット超えでエラー（TOTAL は REAL）、duckdb は HUGEINT に広がる"""
    big = "WITH t(v) AS (VALUES (9223372036854775807), (1))"
    with pytest.raises(sqlite3.OperationalError, match="overflow"):
        run("sqlite", big + " SELECT SUM(v) FROM t")
    assert run("sqlite", big + " SELECT TOTAL(v) FROM t") == [(9.223372036854776e18,)]
    assert run(
        "duckdb", big.replace("(1)", "(1::BIGINT)") + " SELECT SUM(v) FROM t"
    ) == [(9223372036854775808,)]


def test_string_values():
    """sqlite は変換できる文字列を足し、できない文字列は 0。duckdb は VARCHAR 列だとエラー"""
    assert run(
        "sqlite",
        "WITH t(v) AS (VALUES (1), ('2'), ('x')) SELECT SUM(v), typeof(SUM(v)) FROM t",
    ) == [(3.0, "real")]
    with pytest.raises(duckdb.BinderException):
        run("duckdb", "WITH t(v) AS (VALUES ('1'), ('2')) SELECT SUM(v) FROM t")


def test_floating_point_summation():
    """sqlite は 3.43+ の補正付き加算で 0.6 ちょうど、duckdb の DOUBLE は誤差付き、DECIMAL は 0.6。値は版で変わるので許容誤差で比べる"""
    sql = "WITH t(v) AS (VALUES (0.1), (0.2), (0.3)) SELECT SUM(v) FROM t"
    assert run("sqlite", sql)[0][0] == pytest.approx(0.6)
    assert run("duckdb", sql) == [(Decimal("0.6"),)]
    dbl = run(
        "duckdb",
        "WITH t(v) AS (VALUES (0.1::DOUBLE), (0.2::DOUBLE), (0.3::DOUBLE)) SELECT SUM(v) FROM t",
    )[0][0]
    assert dbl == pytest.approx(0.6)
    assert dbl != 0.6
    ten = "WITH t(v) AS (SELECT 0.1 FROM (VALUES (1), (2), (3), (4), (5), (6), (7), (8), (9), (10))) SELECT SUM(v) FROM t"
    total = run("sqlite", ten)[0][0]
    assert total == pytest.approx(1.0)
    if sqlite3.sqlite_version_info >= (3, 43):
        assert run("sqlite", sql) == [(0.6,)]
        assert total == 1.0


@pytest.mark.parametrize("engine", ENGINES)
def test_group_by_sums_per_group(engine):
    """GROUP BY でグループごとの合計。NULL は無視"""
    sql = "WITH t(k, v) AS (VALUES ('a', 1), ('b', 2), ('a', 3), ('b', NULL)) SELECT k, SUM(v) FROM t GROUP BY k ORDER BY k"
    assert run(engine, sql) == [("a", 4), ("b", 2)]


@pytest.mark.parametrize("engine", ENGINES)
def test_missing_count_detects_nulls(engine):
    """Pitfalls: COUNT(*) - COUNT(v) で欠損数が分かる"""
    assert run(engine, DATA + " SELECT COUNT(*) - COUNT(qty) FROM t") == [(1,)]
