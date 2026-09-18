# カード collection-group-by の Contract を検証するテスト
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


DATA = "WITH t(k, v) AS (VALUES ('a', 1), ('b', 2), ('a', 3), (NULL, 4))"


@pytest.mark.parametrize("engine", ENGINES)
def test_groups_by_key_with_null_as_one_group(engine):
    """同じキーが 1 グループ。NULL キーも 1 グループになる（NULL の位置は方言で違う）"""
    sql = (
        DATA
        + " SELECT k, COUNT(*), SUM(v), GROUP_CONCAT(v, ',') FROM t GROUP BY k ORDER BY k"
    )
    rows = run(engine, sql)
    # GROUP_CONCAT の連結順は保証されないので、要素の集合で比べる
    normalized = {(k, n, s, frozenset(items.split(","))) for k, n, s, items in rows}
    expected = {
        ("a", 2, 4, frozenset({"1", "3"})),
        ("b", 1, 2, frozenset({"2"})),
        (None, 1, 4, frozenset({"4"})),
    }
    assert normalized == expected
    null_index = [r[0] for r in rows].index(None)
    assert null_index == (0 if engine == "sqlite" else 2)


@pytest.mark.parametrize("engine", ENGINES)
def test_count_star_counts_null_values_but_count_col_does_not(engine):
    """COUNT(*) は NULL 値の行も数え、COUNT(v) / SUM(v) は NULL を無視する"""
    sql = "WITH t(k, v) AS (VALUES ('a', 1), ('a', NULL)) SELECT k, COUNT(*), COUNT(v), SUM(v) FROM t GROUP BY k"
    assert run(engine, sql) == [("a", 2, 1, 1)]


@pytest.mark.parametrize("engine", ENGINES)
def test_group_concat_over_sorted_subquery_has_no_order_guarantee(engine):
    """並べ替えたサブクエリから集計しても連結順は規格上保証されないので、要素の集合だけを検証する"""
    sql = (
        DATA
        + " SELECT k, GROUP_CONCAT(v, ',') FROM (SELECT k, v FROM t WHERE k = 'a' ORDER BY v DESC) GROUP BY k"
    )
    rows = run(engine, sql)
    assert [(k, frozenset(items.split(","))) for k, items in rows] == [
        ("a", frozenset({"1", "3"}))
    ]


@pytest.mark.parametrize("engine", ENGINES)
def test_group_concat_order_via_window_order_by(engine):
    """3.44 未満でも順序を決められる形: ウィンドウ定義の ORDER BY で集約への入力順を指定する（sqlite 3.25+、duckdb）"""
    sql = (
        DATA + " SELECT DISTINCT k, GROUP_CONCAT(v, ',') OVER"
        " (PARTITION BY k ORDER BY v DESC ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)"
        " FROM t WHERE k = 'a'"
    )
    assert run(engine, sql) == [("a", "3,1")]


@pytest.mark.parametrize("engine", ENGINES)
def test_group_concat_order_is_controlled_by_order_by_inside(engine):
    """GROUP_CONCAT の連結順は中の ORDER BY で決まる（sqlite 3.44+）。duckdb は STRING_AGG も同じ"""
    if engine == "sqlite" and sqlite3.sqlite_version_info < (3, 44):
        pytest.skip("GROUP_CONCAT(... ORDER BY) は sqlite 3.44 以降")
    sql = (
        DATA
        + " SELECT k, GROUP_CONCAT(v, ',' ORDER BY v DESC) FROM t WHERE k = 'a' GROUP BY k"
    )
    assert run(engine, sql) == [("a", "3,1")]
    if engine == "duckdb":
        sql = (
            DATA
            + " SELECT k, STRING_AGG(v, ',' ORDER BY v DESC) FROM t WHERE k = 'a' GROUP BY k"
        )
        assert run(engine, sql) == [("a", "3,1")]


@pytest.mark.parametrize("engine", ENGINES)
def test_empty_input_yields_no_groups_but_one_row_without_group_by(engine):
    """0 行なら GROUP BY 付きは 0 行、GROUP BY 無しは 1 行（COUNT は 0、SUM は NULL）"""
    empty = "WITH t(k, v) AS (SELECT 'a', 1 WHERE 0)"
    assert run(engine, empty + " SELECT k, COUNT(*) FROM t GROUP BY k") == []
    assert run(engine, empty + " SELECT COUNT(*), SUM(v) FROM t") == [(0, None)]


def test_bare_column_is_allowed_in_sqlite_but_error_in_duckdb():
    """裸の列は sqlite では通る（値は不定）が duckdb はエラー。ANY_VALUE なら通る"""
    sql = DATA + " SELECT k, v, COUNT(*) FROM t GROUP BY k ORDER BY k"
    rows = run("sqlite", sql)
    assert [(r[0], r[2]) for r in rows] == [(None, 1), ("a", 2), ("b", 1)]
    with pytest.raises(duckdb.BinderException):
        run("duckdb", sql)
    rows = run(
        "duckdb",
        DATA + " SELECT k, ANY_VALUE(v), COUNT(*) FROM t GROUP BY k ORDER BY k",
    )
    assert [(r[0], r[2]) for r in rows] == [("a", 2), ("b", 1), (None, 1)]


@pytest.mark.parametrize("engine", ENGINES)
def test_key_equality_by_value_and_case_sensitive(engine):
    """1 と 1.0 は同じグループ、'a' と 'A' は別グループ"""
    nums = "WITH t(k) AS (VALUES (1), (1.0)) SELECT COUNT(*) FROM t GROUP BY k"
    assert run(engine, nums) == [(2,)]
    strs = "WITH t(k) AS (VALUES ('a'), ('A')) SELECT k, COUNT(*) FROM t GROUP BY k ORDER BY k"
    assert run(engine, strs) == [("A", 1), ("a", 1)]


@pytest.mark.parametrize("engine", ENGINES)
def test_having_filters_groups(engine):
    """HAVING はグループ化後の絞り込み"""
    sql = DATA + " SELECT k, COUNT(*) FROM t GROUP BY k HAVING COUNT(*) > 1"
    assert run(engine, sql) == [("a", 2)]


@pytest.mark.parametrize("engine", ENGINES)
def test_result_order_without_order_by_is_a_set(engine):
    """ORDER BY 無しの結果は順序を仮定できない（集合として比較する）"""
    sql = "WITH t(k) AS (VALUES ('b'), ('a'), ('b'), ('c'), ('a')) SELECT k, COUNT(*) FROM t GROUP BY k"
    assert set(run(engine, sql)) == {("a", 2), ("b", 2), ("c", 1)}
