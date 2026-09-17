# カード date-diff-days の Contract を検証するテスト
import datetime
import sqlite3

import duckdb
import pytest


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


def jd_diff(d2, d1):
    return f"CAST(JULIANDAY({d2}) - JULIANDAY({d1}) AS INTEGER)"


def test_sqlite_calendar_day_difference_and_sign():
    """sqlite: 日付同士の差は日数。d2 - d1 の符号、同じ日は 0"""
    a, b, c, d = "'2024-03-01'", "'2024-02-28'", "'2025-01-01'", "'2024-01-01'"
    sql = (
        f"SELECT {jd_diff(a, b)}, {jd_diff(b, a)}, {jd_diff(a, a)}, {jd_diff(c, d)},"
        " JULIANDAY('2024-03-01') - JULIANDAY('2024-02-28'), typeof(JULIANDAY('2024-03-01'))"
    )
    assert run("sqlite", sql) == [(2, -2, 0, 366, 2.0, "real")]


def test_sqlite_time_part_must_be_dropped_for_calendar_days():
    """sqlite: 時刻込みだと小数になり CAST で 0。DATE() を挟むと暦日差"""
    t2, t1 = "'2024-03-01 00:30:00'", "'2024-02-29 23:00:00'"
    sql = (
        f"SELECT JULIANDAY({t2}) - JULIANDAY({t1}), {jd_diff(t2, t1)},"
        f" {jd_diff(f'DATE({t2})', f'DATE({t1})')}, {jd_diff(f'DATE({t1})', f'DATE({t2})')}"
    )
    assert run("sqlite", sql) == [(0.0625, 0, 1, -1)]


def test_sqlite_cast_truncates_toward_zero():
    """sqlite: CAST AS INTEGER はゼロ方向。ミリ秒のずれで 1 日落ちるが DATE() で防げる"""
    t2, t1 = "'2024-03-01'", "'2024-02-28 00:00:00.001'"
    sql = (
        f"SELECT {jd_diff(t2, t1)}, {jd_diff(f'DATE({t2})', f'DATE({t1})')},"
        " CAST(-0.9 AS INTEGER), CAST(0.9 AS INTEGER)"
    )
    assert run("sqlite", sql) == [(1, 2, 0, 0)]


def test_sqlite_offset_input_is_converted_to_utc():
    """sqlite: オフセット付き入力は UTC に変換されてから扱われる"""
    sql = "SELECT JULIANDAY('2024-03-01T00:00:00+09:00') - JULIANDAY('2024-03-01'), DATE('2024-03-01T00:00:00+09:00')"
    assert run("sqlite", sql) == [(-0.375, "2024-02-29")]


def test_sqlite_invalid_inputs_give_null():
    """sqlite: 非 ISO・不正・NULL は NULL"""
    sql = "SELECT JULIANDAY('2024/02/29'), JULIANDAY('not a date'), JULIANDAY(NULL), JULIANDAY('2024-03-01') - JULIANDAY(NULL)"
    assert run("sqlite", sql) == [(None, None, None, None)]


def test_sqlite_unixepoch_alternative():
    """sqlite 3.38+: UNIXEPOCH の差を 86400 で整数除算しても同じ"""
    if sqlite3.sqlite_version_info < (3, 38):
        pytest.skip("UNIXEPOCH は sqlite 3.38 以降")
    sql = "SELECT (UNIXEPOCH('2024-03-01') - UNIXEPOCH('2024-02-28')) / 86400, (UNIXEPOCH('2024-02-28') - UNIXEPOCH('2024-03-01')) / 86400"
    assert run("sqlite", sql) == [(2, -2)]


def test_duckdb_date_diff_argument_order_and_type():
    """duckdb: DATE_DIFF('day', 開始, 終了) は BIGINT。DATE 同士の引き算も整数"""
    sql = (
        "SELECT DATE_DIFF('day', DATE '2024-02-28', DATE '2024-03-01'), DATE_DIFF('day', DATE '2024-03-01', DATE '2024-02-28'),"
        " typeof(DATE_DIFF('day', DATE '2024-02-28', DATE '2024-03-01')), DATE_DIFF('day', DATE '2024-03-01', DATE '2024-03-01'),"
        " DATE_DIFF('day', DATE '2024-01-01', DATE '2025-01-01'), DATE '2024-03-01' - DATE '2024-02-28',"
        " typeof(DATE '2024-03-01' - DATE '2024-02-28'), DATEDIFF('day', DATE '2024-02-28', DATE '2024-03-01'),"
        " DATE_DIFF('day', NULL::DATE, DATE '2024-03-01')"
    )
    assert run("duckdb", sql) == [(2, -2, "BIGINT", 0, 366, 2, "BIGINT", 2, None)]


def test_duckdb_timestamps_count_boundaries_not_full_days():
    """duckdb: TIMESTAMP の DATE_DIFF は日付境界をまたいだ回数。DATE_SUB は丸 24 時間の数"""
    sql = (
        "SELECT DATE_DIFF('day', TIMESTAMP '2024-02-29 23:00:00', TIMESTAMP '2024-03-01 00:30:00'),"
        " DATE_DIFF('day', TIMESTAMP '2024-03-01 00:30:00', TIMESTAMP '2024-02-29 23:00:00'),"
        " DATE_DIFF('day', TIMESTAMP '2024-02-29 12:00:00', TIMESTAMP '2024-03-01 11:59:59'),"
        " DATE_SUB('day', TIMESTAMP '2024-02-29 23:00:00', TIMESTAMP '2024-03-01 00:30:00'),"
        " TIMESTAMP '2024-03-01 00:30:00' - TIMESTAMP '2024-02-29 23:00:00',"
        " typeof(TIMESTAMP '2024-03-01 00:30:00' - TIMESTAMP '2024-02-29 23:00:00')"
    )
    assert run("duckdb", sql) == [
        (1, -1, 1, 0, datetime.timedelta(seconds=5400), "INTERVAL")
    ]


def test_elapsed_time_alternative():
    """Alternatives: 実時間の経過は JULIANDAY の差 × 86400 秒"""
    assert run(
        "sqlite",
        "SELECT (JULIANDAY('2024-03-01 00:30:00') - JULIANDAY('2024-02-29 23:00:00')) * 86400",
    ) == [(5400.0,)]
