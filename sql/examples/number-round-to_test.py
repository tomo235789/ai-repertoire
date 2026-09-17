# カード number-round-to の Contract を検証するテスト
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


def as_floats(rows):
    """Decimal / int / float が混ざる結果を float に揃える（値の比較用）"""
    return [tuple(None if v is None else float(v) for v in r) for r in rows]


@pytest.mark.parametrize("engine", ENGINES)
def test_half_rounds_away_from_zero(engine):
    """.5 はゼロから遠い方へ（偶数丸めではない）"""
    sql = "SELECT ROUND(2.5), ROUND(3.5), ROUND(-2.5), ROUND(0.5), ROUND(1.5), ROUND(1.2345, 2)"
    assert as_floats(run(engine, sql)) == [(3.0, 4.0, -3.0, 1.0, 2.0, 1.23)]


SQLITE_VERSION = sqlite3.sqlite_version_info
# ROUND / printf の 10 進変換が変わった版は 3.43.0（ソースからビルドして確認: 3.42.0 は 2.675 → 2.68、3.43.0 / 3.43.1 / 3.43.2 / 3.45.1 は 2.67）
SQLITE_NEW_ROUNDING = SQLITE_VERSION >= (3, 43, 0)


def test_representation_error_differs_by_dialect():
    """sqlite 3.43+ は REAL で 2.675 → 2.67（3.37 は 2.68）、duckdb は DECIMAL で 2.68。duckdb の DOUBLE は値によって誤差が残る"""
    sql = "SELECT ROUND(2.675, 2), ROUND(1.005, 2), ROUND(1.45, 1)"
    expected = (2.67, 1.0, 1.4) if SQLITE_NEW_ROUNDING else (2.68, 1.01, 1.5)
    assert run("sqlite", sql)[0] == pytest.approx(expected)
    assert run("duckdb", sql) == [(Decimal("2.68"), Decimal("1.01"), Decimal("1.5"))]
    assert run("duckdb", "SELECT ROUND(2.675::DOUBLE, 2), ROUND(1.005::DOUBLE, 2)") == [
        (2.68, 1.0)
    ]


@pytest.mark.parametrize("engine", ENGINES)
def test_integer_input_needs_real_division_before_round(engine):
    """Pitfalls: 100 円単位の丸めは x / 100.0。sqlite は x / 100 が整数除算で ROUND の前に切り捨てられる"""
    sql = "WITH t(x) AS (VALUES (1550), (1549)) SELECT ROUND(x / 100.0) * 100, ROUND(x / 100) * 100 FROM t ORDER BY x DESC"
    rows = as_floats(run(engine, sql))
    assert [r[0] for r in rows] == [1600.0, 1500.0]
    assert [r[1] for r in rows] == (
        [1500.0, 1500.0] if engine == "sqlite" else [1600.0, 1500.0]
    )


def test_return_type_sqlite_real_duckdb_follows_input():
    """sqlite は常に REAL、duckdb は入力の型に従う"""
    sql = "SELECT typeof(ROUND(2.5)), typeof(ROUND(2.5, 1)), typeof(ROUND(3)), typeof(ROUND(3, 1))"
    assert run("sqlite", sql) == [("real", "real", "real", "real")]
    assert run("duckdb", sql) == [
        ("DECIMAL(2,0)", "DECIMAL(2,1)", "INTEGER", "INTEGER")
    ]
    assert run("duckdb", "SELECT typeof(ROUND(2.5::DOUBLE, 1))") == [("DOUBLE",)]
    assert run("sqlite", "SELECT ROUND(3), ROUND(2.5, 0)") == [(3.0, 3.0)]


def test_negative_digits_ignored_in_sqlite_but_honored_in_duckdb():
    """負の桁: sqlite は無視、duckdb は 10 の位・100 の位で丸める"""
    sql = "SELECT ROUND(1250, -2), ROUND(25, -1), ROUND(-25, -1), ROUND(2.5, -1)"
    assert run("sqlite", sql) == [(1250.0, 25.0, -25.0, 3.0)]
    assert as_floats(run("duckdb", sql)) == [(1300.0, 30.0, -30.0, 0.0)]


@pytest.mark.parametrize("engine", ENGINES)
def test_null_propagates(engine):
    """x か n が NULL なら NULL"""
    assert run(engine, "SELECT ROUND(NULL), ROUND(NULL, 2), ROUND(1.2, NULL)") == [
        (None, None, None)
    ]


def test_fractional_digits_argument():
    """n に小数: duckdb はエラー、sqlite は整数に切り捨てて使う"""
    with pytest.raises(duckdb.BinderException):
        run("duckdb", "SELECT ROUND(2.5, 1.9)")
    assert run("sqlite", "SELECT ROUND(2.25, 1.9)") == [(2.3,)]


def test_printf_rounding_direction_differs():
    """Alternatives: printf('%.0f', 2.5) は sqlite で '3'（3.43〜3.45.2 は '2'）、duckdb で '2'。'%.2f' の 2.675 は ROUND と同じく版で変わる"""
    rows = run(
        "sqlite",
        "SELECT printf('%.0f', 2.5), printf('%.0f', 3.5), printf('%.2f', 2.675)",
    )
    assert rows[0][2] == ("2.67" if SQLITE_NEW_ROUNDING else "2.68")
    if (3, 43) <= SQLITE_VERSION < (3, 45, 3):
        pytest.skip(
            "この版の sqlite は printf('%.0f') の .5 の扱いが違う（3.45.1 で '2', '3' を確認）"
        )
    assert rows[0][:2] == ("3", "4")
    assert run(
        "duckdb",
        "SELECT printf('%.0f', 2.5::DOUBLE), printf('%.0f', 3.5::DOUBLE), printf('%.2f', 2.675::DOUBLE)",
    ) == [("2", "4", "2.67")]


def test_round_even_only_in_duckdb():
    """Alternatives: ROUND_EVEN は duckdb のみ"""
    assert run(
        "duckdb", "SELECT ROUND_EVEN(2.5::DOUBLE, 0), ROUND_EVEN(3.5::DOUBLE, 0)"
    ) == [(2.0, 4.0)]
    with pytest.raises(sqlite3.OperationalError):
        run("sqlite", "SELECT ROUND_EVEN(2.5, 0)")


@pytest.mark.parametrize("engine", ENGINES)
def test_floor_ceil_trunc(engine):
    """Alternatives: FLOOR / CEIL / TRUNC はどちらでも同じ"""
    assert as_floats(
        run(engine, "SELECT FLOOR(2.5), CEIL(2.5), TRUNC(-2.7), TRUNC(2.7)")
    ) == [(2.0, 3.0, -2.0, 2.0)]


def test_cast_to_integer_truncates_in_sqlite_but_rounds_in_duckdb():
    """Alternatives: CAST AS INTEGER は sqlite で切り捨て、duckdb で四捨五入"""
    sql = "SELECT CAST(-2.7 AS INTEGER), CAST(2.7 AS INTEGER), CAST(2.5 AS INTEGER)"
    assert run("sqlite", sql) == [(-2, 2, 2)]
    assert run("duckdb", sql) == [(-3, 3, 3)]
