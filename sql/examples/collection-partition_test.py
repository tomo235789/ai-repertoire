# カード collection-partition の Contract を検証するテスト
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


DATA = "WITH t(v) AS (VALUES (1), (2), (3), (4), (NULL))"


@pytest.mark.parametrize("engine", ENGINES)
def test_counts_rows_matching_and_not_matching(engine):
    """条件を満たす行・満たさない行をそれぞれ数える。NULL はどちらにも入らない"""
    sql = (
        DATA
        + " SELECT COUNT(*) FILTER (WHERE v % 2 = 0), COUNT(*) FILTER (WHERE NOT (v % 2 = 0)), COUNT(*) FROM t"
    )
    assert run(engine, sql) == [(2, 2, 5)]


@pytest.mark.parametrize("engine", ENGINES)
def test_null_condition_can_be_forced_to_false_side(engine):
    """偽側を NOT COALESCE(cond, FALSE) か cond IS NOT TRUE にすると NULL の行も偽側に入る"""
    sql = (
        DATA + " SELECT COUNT(*) FILTER (WHERE COALESCE(v % 2 = 0, FALSE)),"
        " COUNT(*) FILTER (WHERE NOT COALESCE(v % 2 = 0, FALSE)),"
        " COUNT(*) FILTER (WHERE v % 2 = 0 IS NOT TRUE) FROM t"
    )
    assert run(engine, sql) == [(2, 3, 3)]


@pytest.mark.parametrize("engine", ENGINES)
def test_no_matching_rows_gives_zero_count_and_null_sum(engine):
    """該当 0 件なら COUNT は 0、SUM は NULL"""
    sql = "WITH t(v) AS (VALUES (1), (3)) SELECT COUNT(*) FILTER (WHERE v % 2 = 0), SUM(v) FILTER (WHERE v % 2 = 0) FROM t"
    assert run(engine, sql) == [(0, None)]


@pytest.mark.parametrize("engine", ENGINES)
def test_empty_input_returns_one_row(engine):
    """0 行でも GROUP BY が無ければ 1 行返る"""
    sql = "WITH t(v) AS (SELECT 1 WHERE 0) SELECT COUNT(*) FILTER (WHERE v % 2 = 0), SUM(v) FILTER (WHERE v % 2 = 0) FROM t"
    assert run(engine, sql) == [(0, None)]


@pytest.mark.parametrize("engine", ENGINES)
def test_works_with_sum_group_by_and_window(engine):
    """SUM にも付けられ、GROUP BY や OVER と組み合わせられる"""
    sums = (
        DATA
        + " SELECT SUM(v) FILTER (WHERE v % 2 = 0), SUM(v) FILTER (WHERE v % 2 = 1) FROM t"
    )
    assert run(engine, sums) == [(6, 4)]
    grouped = (
        "WITH t(k, v) AS (VALUES ('a', 1), ('a', 2), ('b', 3))"
        " SELECT k, COUNT(*) FILTER (WHERE v >= 2) FROM t GROUP BY k ORDER BY k"
    )
    assert run(engine, grouped) == [("a", 1), ("b", 1)]
    window = "WITH t(v) AS (VALUES (1), (2), (3), (4)) SELECT v, COUNT(*) FILTER (WHERE v % 2 = 0) OVER () FROM t ORDER BY v"
    assert run(engine, window) == [(1, 2), (2, 2), (3, 2), (4, 2)]


@pytest.mark.parametrize("engine", ENGINES)
def test_sum_case_alternative_matches_filter(engine):
    """Alternatives: SUM(CASE WHEN ...) は FILTER と同じ値。ELSE を省くと該当 0 件で NULL"""
    sql = (
        DATA
        + " SELECT SUM(CASE WHEN v % 2 = 0 THEN 1 ELSE 0 END), SUM(CASE WHEN NOT (v % 2 = 0) THEN 1 ELSE 0 END),"
        " SUM(CASE WHEN v > 100 THEN 1 END) FROM t"
    )
    assert run(engine, sql) == [(2, 2, None)]


@pytest.mark.parametrize("engine", ENGINES)
def test_count_col_filter_ignores_null_values(engine):
    """Pitfalls: COUNT(v) FILTER は v が NULL の行を数えない"""
    sql = "WITH t(v) AS (VALUES (2), (NULL)) SELECT COUNT(*) FILTER (WHERE v IS NULL), COUNT(v) FILTER (WHERE v IS NULL) FROM t"
    assert run(engine, sql) == [(1, 0)]
