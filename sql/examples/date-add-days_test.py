# カード date-add-days の Contract を検証するテスト
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


def test_sqlite_adds_days_across_month_and_year_boundaries():
    """sqlite: 月末・年末・うるう年をカレンダーどおり繰り越す。返り値は TEXT"""
    sql = (
        "SELECT DATE('2024-02-28', '+1 day'), DATE('2024-02-29', '+1 day'), DATE('2024-12-31', '+1 day'),"
        " DATE('2024-02-29', '-1 day'), DATE('2024-02-29', '+365 days'), DATE('2024-02-29', '+0 days'),"
        " typeof(DATE('2024-02-29', '+1 day'))"
    )
    assert run("sqlite", sql) == [
        (
            "2024-02-29",
            "2024-03-01",
            "2025-01-01",
            "2024-02-28",
            "2025-02-28",
            "2024-02-29",
            "text",
        )
    ]


def test_sqlite_modifier_spelling():
    """sqlite: day / days・符号無しは可。空白の位置が違うと NULL"""
    sql = (
        "SELECT DATE('2024-02-29', '+1 days'), DATE('2024-02-29', '1 day'), DATE('2024-02-29', '+1day'),"
        " DATE('2024-02-29', '+ 1 day'), DATE('2024-02-29', '+-1 day'), DATE('2024-02-29', '+1 day', '+1 day')"
    )
    assert run("sqlite", sql) == [
        ("2024-03-01", "2024-03-01", None, None, None, "2024-03-02")
    ]


def test_sqlite_time_part_and_fractional_days():
    """sqlite: DATE は日付だけ、DATETIME は時刻を保つ。'+1.5 days' は 36 時間"""
    sql = (
        "SELECT DATE('2024-02-29 23:30:00', '+1 day'), DATETIME('2024-02-29 23:30:00', '+1 day'),"
        " DATETIME('2024-02-29', '+1.5 days'), DATE('2024-02-29', '+1.5 days')"
    )
    assert run("sqlite", sql) == [
        ("2024-03-01", "2024-03-01 23:30:00", "2024-03-01 12:00:00", "2024-03-01")
    ]


def test_sqlite_month_and_year_are_normalized():
    """sqlite: '+1 month' / '+1 year' は正規化して繰り越す。'floor' で月末に丸める（3.46+）"""
    sql = "SELECT DATE('2024-01-31', '+1 month'), DATE('2024-02-29', '+1 year'), DATE('2024-01-31', '+1 month', '-1 day')"
    assert run("sqlite", sql) == [("2024-03-02", "2025-03-01", "2024-03-01")]
    if sqlite3.sqlite_version_info >= (3, 46):
        sql = "SELECT DATE('2024-01-31', '+1 month', 'floor'), DATE('2024-02-29', '+1 year', 'floor')"
        assert run("sqlite", sql) == [("2024-02-29", "2025-02-28")]


def test_sqlite_invalid_inputs_and_range():
    """sqlite: 非 ISO・不正・NULL は NULL、無い日付は正規化、9999-12-31 の翌日は NULL"""
    sql = (
        "SELECT DATE('2024/02/29', '+1 day'), DATE('not a date', '+1 day'), DATE(NULL, '+1 day'),"
        " DATE('2024-02-30', '+1 day'), DATE('9999-12-31', '+1 day')"
    )
    assert run("sqlite", sql) == [(None, None, None, "2024-03-02", None)]


def test_sqlite_building_modifier_from_a_number():
    """sqlite: 文字列連結は負数で壊れる。printf('%+d days') なら安全"""
    sql = "SELECT DATE('2024-02-29', '+' || 3 || ' days'), DATE('2024-02-29', '+' || -3 || ' days'), DATE('2024-02-29', printf('%+d days', -3))"
    assert run("sqlite", sql) == [("2024-03-03", None, "2024-02-26")]


def test_duckdb_interval_returns_timestamp_and_integer_keeps_date():
    """duckdb: DATE + INTERVAL は TIMESTAMP、DATE + 整数は DATE。::DATE で戻せる"""
    sql = (
        "SELECT DATE '2024-02-29' + INTERVAL 1 DAY, typeof(DATE '2024-02-29' + INTERVAL 1 DAY),"
        " DATE '2024-02-29' + 1, typeof(DATE '2024-02-29' + 1), DATE '2024-02-29' - 1,"
        " (DATE '2024-02-29' + INTERVAL 1 DAY)::DATE, DATE '2024-02-29' + INTERVAL 1 DAY = DATE '2024-03-01'"
    )
    assert run("duckdb", sql) == [
        (
            datetime.datetime(2024, 3, 1, 0, 0),
            "TIMESTAMP",
            datetime.date(2024, 3, 1),
            "DATE",
            datetime.date(2024, 2, 28),
            datetime.date(2024, 3, 1),
            True,
        )
    ]


def test_duckdb_calendar_rollover_and_month_clamp():
    """duckdb: 日の繰り越しはカレンダーどおり、月は月末にクランプ（sqlite と逆）"""
    sql = (
        "SELECT (DATE '2024-02-29' + INTERVAL 365 DAY)::DATE, (DATE '2024-01-31' + INTERVAL 1 MONTH)::DATE,"
        " (DATE '2024-02-29' + INTERVAL 1 YEAR)::DATE, (TIMESTAMP '2024-02-29 23:30:00' + INTERVAL 1 DAY)::VARCHAR"
    )
    assert run("duckdb", sql) == [
        (
            datetime.date(2025, 2, 28),
            datetime.date(2024, 2, 29),
            datetime.date(2025, 2, 28),
            "2024-03-01 23:30:00",
        )
    ]


def test_duckdb_fractional_interval_and_column_days():
    """duckdb: INTERVAL 1.5 DAY は構文エラー、INTERVAL '1.5 days' は 36 時間。列の日数は INTERVAL (n) DAY / to_days(n)"""
    with pytest.raises(duckdb.ParserException):
        run("duckdb", "SELECT DATE '2024-02-29' + INTERVAL 1.5 DAY")
    assert run(
        "duckdb", "SELECT (DATE '2024-02-29' + INTERVAL '1.5 days')::VARCHAR"
    ) == [("2024-03-01 12:00:00",)]
    rows = run(
        "duckdb",
        "SELECT (DATE '2024-02-29' + INTERVAL (n) DAY)::DATE, (DATE '2024-02-29' + to_days(n))::DATE FROM (VALUES (1), (3)) AS t(n)",
    )
    assert rows == [
        (datetime.date(2024, 3, 1), datetime.date(2024, 3, 1)),
        (datetime.date(2024, 3, 3), datetime.date(2024, 3, 3)),
    ]


def test_duckdb_invalid_inputs():
    """duckdb: 文字列リテラル + INTERVAL は Binder Error、無い日付は Conversion Error、NULL は NULL、9999-12-31 + 1 は 10000-01-01"""
    with pytest.raises(duckdb.BinderException):
        run("duckdb", "SELECT '2024-02-29' + INTERVAL 1 DAY")
    with pytest.raises(duckdb.ConversionException):
        run("duckdb", "SELECT DATE '2024-02-30' + INTERVAL 1 DAY")
    assert run(
        "duckdb", "SELECT NULL::DATE + INTERVAL 1 DAY, (DATE '9999-12-31' + 1)::VARCHAR"
    ) == [(None, "10000-01-01")]


def test_end_of_month_alternative_in_sqlite():
    """Alternatives: 月末は 'start of month', '+2 months', '-1 day'"""
    assert run(
        "sqlite", "SELECT DATE('2024-02-10', 'start of month', '+2 months', '-1 day')"
    ) == [("2024-03-31",)]
