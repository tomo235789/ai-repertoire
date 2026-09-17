# カード collection-sort-by の Contract を検証するテスト
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


DATA = "WITH t(name, age) AS (VALUES ('b', 30), ('a', 30), ('c', 20), ('d', NULL))"


@pytest.mark.parametrize("engine", ENGINES)
def test_multiple_keys_compare_left_to_right(engine):
    """左のキーが等しいときだけ次のキーで比較する"""
    sql = DATA + " SELECT name, age FROM t ORDER BY age NULLS LAST, name"
    assert run(engine, sql) == [("c", 20), ("a", 30), ("b", 30), ("d", None)]


@pytest.mark.parametrize("engine", ENGINES)
def test_default_null_position_differs_by_dialect(engine):
    """既定の NULL 位置: sqlite は最小（ASC で先頭）、duckdb は方向によらず末尾"""
    asc = run(engine, DATA + " SELECT name FROM t ORDER BY age, name")
    desc = run(engine, DATA + " SELECT name FROM t ORDER BY age DESC, name")
    if engine == "sqlite":
        assert asc == [("d",), ("c",), ("a",), ("b",)]
    else:
        assert asc == [("c",), ("a",), ("b",), ("d",)]
    assert desc == [("a",), ("b",), ("c",), ("d",)]


@pytest.mark.parametrize("engine", ENGINES)
def test_nulls_first_last_make_dialects_agree(engine):
    """NULLS FIRST / NULLS LAST を書けば方言によらず同じ。IS NULL を先頭キーにしても同じ"""
    first = run(engine, DATA + " SELECT name FROM t ORDER BY age NULLS FIRST, name")
    last = run(engine, DATA + " SELECT name FROM t ORDER BY age NULLS LAST, name")
    portable = run(engine, DATA + " SELECT name FROM t ORDER BY age IS NULL, age, name")
    assert first == [("d",), ("c",), ("a",), ("b",)]
    assert last == [("c",), ("a",), ("b",), ("d",)]
    assert portable == last


@pytest.mark.parametrize("engine", ENGINES)
def test_string_order_is_bytewise_unless_collate_nocase(engine):
    """文字列は大文字が先。COLLATE NOCASE で大小無視（同値の順は不定なので集合で比較）"""
    names = "WITH t(name) AS (VALUES ('b'), ('B'), ('a'), ('A'))"
    assert run(engine, names + " SELECT name FROM t ORDER BY name") == [
        ("A",),
        ("B",),
        ("a",),
        ("b",),
    ]
    rows = run(engine, names + " SELECT name FROM t ORDER BY name COLLATE NOCASE")
    assert [r[0].lower() for r in rows] == ["a", "a", "b", "b"]
    lower = run(engine, names + " SELECT name FROM t ORDER BY LOWER(name), name")
    assert lower == [("A",), ("a",), ("B",), ("b",)]


@pytest.mark.parametrize("engine", ENGINES)
def test_numeric_strings_sort_lexicographically(engine):
    """数値文字列は辞書順。CAST すれば数値順"""
    sql = (
        "WITH t(age) AS (VALUES ('30'), ('9'), ('200')) SELECT age FROM t ORDER BY age"
    )
    assert run(engine, sql) == [("200",), ("30",), ("9",)]
    sql = "WITH t(age) AS (VALUES ('30'), ('9'), ('200')) SELECT age FROM t ORDER BY CAST(age AS INTEGER)"
    assert run(engine, sql) == [("9",), ("30",), ("200",)]


@pytest.mark.parametrize("engine", ENGINES)
def test_ties_are_unordered_so_add_unique_key(engine):
    """同順位の行の順序は不定。一意キーを足せば固定される"""
    sql = DATA + " SELECT name FROM t WHERE age = 30 ORDER BY age"
    assert set(run(engine, sql)) == {("a",), ("b",)}
    sql = DATA + " SELECT name FROM t WHERE age = 30 ORDER BY age, name"
    assert run(engine, sql) == [("a",), ("b",)]


@pytest.mark.parametrize("engine", ENGINES)
def test_column_position_and_limit(engine):
    """列番号でも指定でき、LIMIT で先頭 n 件"""
    sql = DATA + " SELECT name, age FROM t WHERE age IS NOT NULL ORDER BY 2, 1"
    assert run(engine, sql) == [("c", 20), ("a", 30), ("b", 30)]
    sql = DATA + " SELECT name, age FROM t WHERE age IS NOT NULL ORDER BY 2, 1 LIMIT 1"
    assert run(engine, sql) == [("c", 20)]


@pytest.mark.parametrize("engine", ENGINES)
def test_outer_order_by_wins_over_subquery(engine):
    """サブクエリの ORDER BY は外側の順序を決めない"""
    sql = "WITH t(name, age) AS (VALUES ('x', 3), ('y', 2), ('z', 1)) SELECT name FROM (SELECT * FROM t ORDER BY age) ORDER BY name"
    assert run(engine, sql) == [("x",), ("y",), ("z",)]


@pytest.mark.parametrize("engine", ENGINES)
def test_empty_input(engine):
    """0 行なら 0 行"""
    sql = "WITH t(name, age) AS (SELECT 'a', 1 WHERE 0) SELECT name FROM t ORDER BY age, name"
    assert run(engine, sql) == []
