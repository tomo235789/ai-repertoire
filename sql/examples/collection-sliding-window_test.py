# カード collection-sliding-window の Contract を検証するテスト
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


DATA = "WITH t(d, v) AS (VALUES (1, 10), (2, 20), (3, 30), (4, 40), (5, 50))"
FRAME = "ROWS BETWEEN 2 PRECEDING AND CURRENT ROW"


@pytest.mark.parametrize("engine", ENGINES)
def test_moving_average_with_short_leading_windows(engine):
    """直前 2 行 + 自分の平均。先頭は窓が短くなり、捨てられも埋められもしない"""
    sql = DATA + f" SELECT d, AVG(v) OVER (ORDER BY d {FRAME}) FROM t ORDER BY d"
    assert run(engine, sql) == [(1, 10.0), (2, 15.0), (3, 20.0), (4, 30.0), (5, 40.0)]


@pytest.mark.parametrize("engine", ENGINES)
def test_window_row_count_and_sum(engine):
    """COUNT(*) OVER で窓の行数が取れる。SUM は整数のまま"""
    sql = (
        DATA
        + f" SELECT d, SUM(v) OVER (ORDER BY d {FRAME}), COUNT(*) OVER (ORDER BY d {FRAME}) FROM t ORDER BY d"
    )
    assert run(engine, sql) == [
        (1, 10, 1),
        (2, 30, 2),
        (3, 60, 3),
        (4, 90, 3),
        (5, 120, 3),
    ]


@pytest.mark.parametrize("engine", ENGINES)
def test_incomplete_windows_can_be_nulled_via_window_clause(engine):
    """WINDOW 句と CASE で満たない窓を NULL にできる"""
    sql = (
        DATA + " SELECT d, CASE WHEN COUNT(*) OVER w = 3 THEN AVG(v) OVER w END FROM t"
        f" WINDOW w AS (ORDER BY d {FRAME}) ORDER BY d"
    )
    assert run(engine, sql) == [(1, None), (2, None), (3, 20.0), (4, 30.0), (5, 40.0)]


@pytest.mark.parametrize("engine", ENGINES)
def test_rows_vs_range_with_gaps_and_ties(engine):
    """ROWS は行数、RANGE は値の範囲（飛びで減り、同値をまとめて含む）"""
    gaps = (
        "WITH t(d, v) AS (VALUES (1, 10), (2, 20), (4, 40), (5, 50))"
        f" SELECT d, SUM(v) OVER (ORDER BY d {FRAME}), SUM(v) OVER (ORDER BY d RANGE BETWEEN 2 PRECEDING AND CURRENT ROW)"
        " FROM t ORDER BY d"
    )
    assert run(engine, gaps) == [(1, 10, 10), (2, 30, 30), (4, 70, 60), (5, 110, 90)]
    # ROWS の ORDER BY は同値の並びを決めるため一意キー (d, v) にする。RANGE は d の同値をまとめて含む
    ties = (
        "WITH t(d, v) AS (VALUES (1, 20), (1, 10), (2, 30), (3, 40))"
        " SELECT d, v, SUM(v) OVER (ORDER BY d, v ROWS BETWEEN 1 PRECEDING AND CURRENT ROW),"
        " SUM(v) OVER (ORDER BY d RANGE BETWEEN 1 PRECEDING AND CURRENT ROW), SUM(v) OVER (ORDER BY d)"
        " FROM t ORDER BY d, v"
    )
    assert run(engine, ties) == [
        (1, 10, 10, 30, 30),
        (1, 20, 30, 30, 30),
        (2, 30, 50, 60, 60),
        (3, 40, 70, 70, 100),
    ]


DATE_ROWS = "(VALUES ('2024-01-01', 10), ('2024-01-02', 20), ('2024-01-04', 40), ('2024-01-05', 50))"
# duckdb は DATE 型のキーにする
DATE_ROWS_DUCK = DATE_ROWS.replace("'2024", "DATE '2024")


def test_range_needs_numeric_key_and_dates_use_julianday_or_interval():
    """RANGE の幅は数値キー向け。日付文字列は sqlite が黙って違う窓を返し、duckdb はエラー。JULIANDAY / INTERVAL で数値・日付型にする"""
    text_key = (
        f"WITH t(d, v) AS {DATE_ROWS} SELECT d, SUM(v) OVER (ORDER BY d RANGE BETWEEN 2 PRECEDING AND CURRENT ROW)"
        " FROM t ORDER BY d"
    )
    assert run("sqlite", text_key) == [
        ("2024-01-01", 10),
        ("2024-01-02", 20),
        ("2024-01-04", 40),
        ("2024-01-05", 50),
    ]
    with pytest.raises(duckdb.BinderException):
        run("duckdb", text_key)
    julian = (
        f"WITH t(d, v) AS {DATE_ROWS} SELECT d, SUM(v) OVER (ORDER BY JULIANDAY(d) RANGE BETWEEN 2 PRECEDING AND CURRENT ROW)"
        " FROM t ORDER BY d"
    )
    expected = [
        ("2024-01-01", 10),
        ("2024-01-02", 30),
        ("2024-01-04", 60),
        ("2024-01-05", 90),
    ]
    assert run("sqlite", julian) == expected
    interval = (
        f"WITH t(d, v) AS {DATE_ROWS_DUCK}"
        " SELECT d::VARCHAR, SUM(v) OVER (ORDER BY d RANGE BETWEEN INTERVAL 2 DAY PRECEDING AND CURRENT ROW),"
        " SUM(v) OVER (ORDER BY d RANGE BETWEEN INTERVAL '2 days' PRECEDING AND CURRENT ROW) FROM t ORDER BY d"
    )
    assert run("duckdb", interval) == [(d, s, s) for d, s in expected]


@pytest.mark.parametrize("engine", ENGINES)
def test_null_values_are_excluded_from_avg(engine):
    """NULL は分子にも分母にも入らない"""
    sql = (
        "WITH t(d, v) AS (VALUES (1, 10), (2, NULL), (3, 30))"
        " SELECT d, AVG(v) OVER (ORDER BY d ROWS BETWEEN 1 PRECEDING AND CURRENT ROW),"
        " COUNT(v) OVER (ORDER BY d ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) FROM t ORDER BY d"
    )
    assert run(engine, sql) == [(1, 10.0, 1), (2, 10.0, 1), (3, 30.0, 1)]


@pytest.mark.parametrize("engine", ENGINES)
def test_partition_by_restarts_window_per_group(engine):
    """PARTITION BY でグループごとに窓が区切られる"""
    sql = (
        "WITH t(g, d, v) AS (VALUES ('a', 1, 10), ('a', 2, 20), ('b', 1, 30), ('b', 2, 40))"
        " SELECT g, d, SUM(v) OVER (PARTITION BY g ORDER BY d ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) FROM t ORDER BY g, d"
    )
    assert run(engine, sql) == [("a", 1, 10), ("a", 2, 30), ("b", 1, 30), ("b", 2, 70)]


@pytest.mark.parametrize("engine", ENGINES)
def test_avg_of_integers_is_real(engine):
    """整数列でも AVG は実数"""
    sql = "WITH t(d, v) AS (VALUES (1, 1), (2, 2), (3, 4)) SELECT AVG(v) OVER (ORDER BY d ROWS BETWEEN 1 PRECEDING AND CURRENT ROW) FROM t ORDER BY d"
    rows = run(engine, sql)
    assert rows == [(1.0,), (1.5,), (3.0,)]
    assert all(isinstance(r[0], float) for r in rows)


@pytest.mark.parametrize("engine", ENGINES)
def test_shorthand_centered_and_dropping_incomplete(engine):
    """Alternatives: ROWS n PRECEDING の省略形、中心窓、ROW_NUMBER で満たない窓を落とす"""
    short = DATA + " SELECT AVG(v) OVER (ORDER BY d ROWS 2 PRECEDING) FROM t ORDER BY d"
    assert run(engine, short) == [(10.0,), (15.0,), (20.0,), (30.0,), (40.0,)]
    centered = (
        DATA
        + " SELECT SUM(v) OVER (ORDER BY d ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING) FROM t ORDER BY d"
    )
    assert run(engine, centered) == [(30,), (60,), (90,), (120,), (90,)]
    dropped = (
        DATA
        + f" SELECT d, ma3 FROM (SELECT d, AVG(v) OVER (ORDER BY d {FRAME}) AS ma3,"
        " ROW_NUMBER() OVER (ORDER BY d) AS rn FROM t) WHERE rn >= 3 ORDER BY d"
    )
    assert run(engine, dropped) == [(3, 20.0), (4, 30.0), (5, 40.0)]


@pytest.mark.parametrize("engine", ENGINES)
def test_empty_input(engine):
    """0 行なら 0 行"""
    sql = f"WITH t(d, v) AS (SELECT 1, 1 WHERE 0) SELECT AVG(v) OVER (ORDER BY d {FRAME}) FROM t"
    assert run(engine, sql) == []
