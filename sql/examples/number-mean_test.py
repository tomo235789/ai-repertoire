# カード number-mean の Contract を検証するテスト
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


DATA = "WITH t(v) AS (VALUES (1), (2), (NULL), (4))"


@pytest.mark.parametrize("engine", ENGINES)
def test_null_is_excluded_from_numerator_and_denominator(engine):
    """NULL は分子にも分母にも入らない。COUNT(*) で割ると一致しない"""
    rows = run(
        engine,
        DATA + " SELECT AVG(v), SUM(v) * 1.0 / COUNT(*), COUNT(v), COUNT(*) FROM t",
    )
    assert rows[0][0] == pytest.approx(7 / 3)
    assert float(rows[0][1]) == pytest.approx(1.75)
    assert rows[0][2:] == (3, 4)
    assert run(engine, DATA + " SELECT AVG(COALESCE(v, 0)) FROM t") == [(1.75,)]


@pytest.mark.parametrize("engine", ENGINES)
def test_empty_or_all_null_gives_null(engine):
    """0 行・全部 NULL なら NULL"""
    assert run(engine, "WITH t(v) AS (SELECT 1 WHERE 0) SELECT AVG(v) FROM t") == [
        (None,)
    ]
    assert run(engine, "WITH t(v) AS (VALUES (NULL), (NULL)) SELECT AVG(v) FROM t") == [
        (None,)
    ]


def test_integer_column_returns_real():
    """整数列でも実数。sqlite は REAL、duckdb は DOUBLE（DECIMAL 列でも）"""
    sql = "WITH t(v) AS (VALUES (1), (2)) SELECT AVG(v), typeof(AVG(v)) FROM t"
    assert run("sqlite", sql) == [(1.5, "real")]
    assert run("duckdb", sql) == [(1.5, "DOUBLE")]
    dec = "WITH t(v) AS (VALUES (1.5::DECIMAL(10,2)), (2.5::DECIMAL(10,2))) SELECT AVG(v), typeof(AVG(v)) FROM t"
    assert run("duckdb", dec) == [(2.0, "DOUBLE")]


def test_sum_divided_by_count_differs_by_dialect():
    """SUM / COUNT は sqlite で整数除算、duckdb は実数除算（整数除算は //）"""
    sql = "WITH t(v) AS (VALUES (1), (2)) SELECT SUM(v) / COUNT(v) FROM t"
    assert run("sqlite", sql) == [(1,)]
    assert run("duckdb", sql) == [(1.5,)]
    assert run(
        "duckdb", "WITH t(v) AS (VALUES (1), (2)) SELECT SUM(v) // COUNT(v) FROM t"
    ) == [(1,)]
    assert run(
        "sqlite", "WITH t(v) AS (VALUES (1), (2)) SELECT SUM(v) * 1.0 / COUNT(v) FROM t"
    ) == [(1.5,)]


def test_floating_point_representation():
    """0.1, 0.2, 0.3 の平均: sqlite は 0.2 に誤差が乗る（最下位桁は版で変わり得る）、duckdb は DECIMAL で 0.2、DOUBLE で誤差付き"""
    sql = "WITH t(v) AS (VALUES (0.1), (0.2), (0.3)) SELECT AVG(v) FROM t"
    assert run("sqlite", sql)[0][0] == pytest.approx(0.2)
    assert run("duckdb", sql) == [(0.2,)]
    dbl = "WITH t(v) AS (VALUES (0.1::DOUBLE), (0.2::DOUBLE), (0.3::DOUBLE)) SELECT AVG(v) FROM t"
    assert run("duckdb", dbl)[0][0] == pytest.approx(0.2)


def test_string_values():
    """sqlite は変換できない文字列を 0 として数える。duckdb は VARCHAR 列でエラー"""
    assert run("sqlite", "WITH t(v) AS (VALUES (1), ('x')) SELECT AVG(v) FROM t") == [
        (0.5,)
    ]
    with pytest.raises(duckdb.BinderException):
        run("duckdb", "WITH t(v) AS (VALUES ('1'), ('x')) SELECT AVG(v) FROM t")


@pytest.mark.parametrize("engine", ENGINES)
def test_group_by(engine):
    """GROUP BY でグループごとの平均。NULL は無視"""
    sql = "WITH t(k, v) AS (VALUES ('a', 1), ('b', 2), ('a', 3), ('b', NULL)) SELECT k, AVG(v) FROM t GROUP BY k ORDER BY k"
    assert run(engine, sql) == [("a", 2.0), ("b", 2.0)]


@pytest.mark.parametrize("engine", ENGINES)
def test_weighted_mean_alternative(engine):
    """Alternatives: 加重平均は SUM(v * w) / SUM(w)（sqlite は * 1.0 で実数化）"""
    sql = "WITH t(v, w) AS (VALUES (1, 1), (4, 3)) SELECT SUM(v * w) * 1.0 / SUM(w) FROM t"
    assert float(run(engine, sql)[0][0]) == 3.25


def test_median():
    """Alternatives: MEDIAN は duckdb にある。sqlite は SQLITE_ENABLE_PERCENTILE 付きビルドだけ（あれば同じ値）"""
    sql = "WITH t(v) AS (VALUES (1), (2), (10)) SELECT MEDIAN(v) FROM t"
    assert run("duckdb", sql) == [(2.0,)]
    try:
        rows = run("sqlite", sql)
    except sqlite3.OperationalError:
        pytest.skip("この sqlite に MEDIAN は無い")
    assert rows == [(2.0,)]


def test_decimal_literal_result_is_decimal_in_duckdb():
    """duckdb の Usage の SUM(v) * 1.0 / COUNT(*) は DOUBLE として返る"""
    rows = run("duckdb", DATA + " SELECT typeof(SUM(v) * 1.0 / COUNT(*)) FROM t")
    assert rows == [("DOUBLE",)]
    assert not isinstance(run("duckdb", DATA + " SELECT AVG(v) FROM t")[0][0], Decimal)
