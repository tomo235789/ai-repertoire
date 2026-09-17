# カード date-start-of-day の Contract を検証するテスト
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


def run_duckdb_with_timezone(tz, sql):
    """duckdb で TimeZone を設定してから SQL を実行する（ICU が無ければスキップ）"""
    con = duckdb.connect()
    try:
        try:
            con.execute(f"SET TimeZone = '{tz}'")
        except duckdb.Error:
            pytest.skip("この duckdb では TimeZone を設定できない")
        return con.execute(sql).fetchall()
    finally:
        con.close()


def test_sqlite_date_and_start_of_day_are_text():
    """sqlite: DATE は日付、DATETIME 'start of day' は 0 時。どちらも TEXT"""
    sql = (
        "SELECT DATE('2024-02-29 13:45:07'), DATETIME('2024-02-29 13:45:07', 'start of day'),"
        " typeof(DATE('2024-02-29 13:45:07')), typeof(DATETIME('2024-02-29 13:45:07', 'start of day')),"
        " DATE('2024-02-29T13:45:07'), DATE(1709214307, 'unixepoch')"
    )
    assert run("sqlite", sql) == [
        (
            "2024-02-29",
            "2024-02-29 00:00:00",
            "text",
            "text",
            "2024-02-29",
            "2024-02-29",
        )
    ]


def test_sqlite_idempotent():
    """sqlite: 0 時の入力や日付だけの入力でも同じ値（冪等）"""
    sql = (
        "SELECT DATE(DATE('2024-02-29 13:45:07')), DATETIME('2024-02-29 00:00:00', 'start of day'),"
        " DATETIME('2024-02-29', 'start of day'), DATE('2024-02-29 13:45:07', 'start of day')"
    )
    assert run("sqlite", sql) == [
        ("2024-02-29", "2024-02-29 00:00:00", "2024-02-29 00:00:00", "2024-02-29")
    ]


def test_sqlite_subsecond():
    """sqlite: 秒未満は切り捨て、23:59:59.999 は同じ日"""
    sql = "SELECT DATE('2024-02-29 13:45:07.999'), DATE('2024-02-29 23:59:59.999')"
    assert run("sqlite", sql) == [("2024-02-29", "2024-02-29")]


def test_sqlite_utc_and_offset_handling():
    """sqlite: オフセット付きは UTC に変換、'+9 hours' で JST の日付、'localtime' → 'utc' で戻る"""
    sql = (
        "SELECT DATE('2024-03-01 08:45:07+09:00'), DATE('2024-02-29 23:45:07', '+9 hours'), DATE('2024-02-29 13:45:07', '+9 hours'),"
        " DATE('2024-02-29 13:45:07', 'localtime', 'utc')"
    )
    assert run("sqlite", sql) == [
        ("2024-02-29", "2024-03-01", "2024-02-29", "2024-02-29")
    ]


def test_sqlite_invalid_inputs_give_null():
    """sqlite: 非 ISO・不正・NULL は NULL"""
    assert run(
        "sqlite", "SELECT DATE('2024/02/29 13:45:07'), DATE('not a date'), DATE(NULL)"
    ) == [(None, None, None)]


def test_sqlite_string_comparison_holds_only_for_normalized_text():
    """sqlite: 文字列比較が時系列順になるのは両辺が DATETIME() の形のときだけ。日付だけ・オフセット付きの生文字列とは噛み合わない"""
    sql = (
        "SELECT DATETIME('2024-02-29 13:45:07', 'start of day') <= '2024-02-29 13:45:07',"
        " DATETIME('2024-02-29', 'start of day') <= '2024-02-29',"
        " DATETIME('2024-02-29', 'start of day') <= DATETIME('2024-02-29'),"
        " DATETIME('2024-03-01 08:45:07+09:00', 'start of day'),"
        " DATETIME('2024-03-01 08:45:07+09:00', 'start of day') <= DATETIME('2024-03-01 08:45:07+09:00')"
    )
    assert run("sqlite", sql) == [(1, 0, 1, "2024-02-29 00:00:00", 1)]


def test_sqlite_modifier_chains():
    """sqlite: 修飾子は左から適用"""
    sql = (
        "SELECT DATETIME('2024-02-29 13:45:07', 'start of day', '+1 day'), DATETIME('2024-02-29 13:45:07', 'start of day', '+1 day', '-1 second'),"
        " DATETIME('2024-02-29 13:45:07', 'start of month'), DATETIME('2024-02-29 13:45:07', 'start of year')"
    )
    assert run("sqlite", sql) == [
        (
            "2024-03-01 00:00:00",
            "2024-02-29 23:59:59",
            "2024-02-01 00:00:00",
            "2024-01-01 00:00:00",
        )
    ]


def test_duckdb_date_trunc_is_timestamp_and_cast_is_date():
    """duckdb: DATE_TRUNC は TIMESTAMP（DATE 入力も 1.5.0 から TIMESTAMP）、::DATE は DATE。冪等で NULL は NULL"""
    sql = (
        "SELECT DATE_TRUNC('day', TIMESTAMP '2024-02-29 13:45:07'), typeof(DATE_TRUNC('day', TIMESTAMP '2024-02-29 13:45:07')),"
        " (TIMESTAMP '2024-02-29 13:45:07')::DATE, typeof((TIMESTAMP '2024-02-29 13:45:07')::DATE),"
        " typeof(DATE_TRUNC('day', DATE '2024-02-29')), DATE_TRUNC('day', NULL::TIMESTAMP),"
        " DATE_TRUNC('day', DATE_TRUNC('day', TIMESTAMP '2024-02-29 13:45:07')) = DATE_TRUNC('day', TIMESTAMP '2024-02-29 13:45:07'),"
        " DATE_TRUNC('day', TIMESTAMP '2024-02-29 23:59:59.999')::VARCHAR, DATE_TRUNC('day', TIMESTAMP '2024-02-29 13:45:07') = DATE '2024-02-29'"
    )
    assert run("duckdb", sql) == [
        (
            datetime.datetime(2024, 2, 29, 0, 0),
            "TIMESTAMP",
            datetime.date(2024, 2, 29),
            "DATE",
            "TIMESTAMP",
            None,
            True,
            "2024-02-29 00:00:00",
            True,
        )
    ]


def test_duckdb_unit_spelling_and_string_literal():
    """duckdb: 'day' / 'days' / 'DAY' はどれも可。文字列リテラルはキャストが要る"""
    sql = "SELECT DATE_TRUNC('days', TIMESTAMP '2024-02-29 13:45:07')::VARCHAR, DATE_TRUNC('DAY', '2024-02-29 13:45:07'::TIMESTAMP)::VARCHAR"
    assert run("duckdb", sql) == [("2024-02-29 00:00:00", "2024-02-29 00:00:00")]
    with pytest.raises(duckdb.BinderException):
        run("duckdb", "SELECT DATE_TRUNC('day', '2024-02-29 13:45:07')")


def test_duckdb_timestamptz_truncates_in_session_timezone():
    """duckdb: TIMESTAMPTZ は TimeZone 設定のローカル日で切られる。AT TIME ZONE 'UTC' で固定"""
    sql = (
        "SELECT DATE_TRUNC('day', TIMESTAMPTZ '2024-03-01 08:45:07+09:00')::VARCHAR,"
        " DATE_TRUNC('day', TIMESTAMPTZ '2024-03-01 08:45:07+09:00' AT TIME ZONE 'UTC')::VARCHAR,"
        " typeof(DATE_TRUNC('day', TIMESTAMPTZ '2024-03-01 08:45:07+09:00'))"
    )
    assert run_duckdb_with_timezone("UTC", sql) == [
        ("2024-02-29 00:00:00+00", "2024-02-29 00:00:00", "TIMESTAMP WITH TIME ZONE")
    ]
    assert run_duckdb_with_timezone("Asia/Tokyo", sql) == [
        ("2024-03-01 00:00:00+09", "2024-02-29 00:00:00", "TIMESTAMP WITH TIME ZONE")
    ]


def test_day_range_alternative():
    """Alternatives: その日の範囲は >= DATE(x) AND < DATE(x, '+1 day')。オフセット付きの列は DATETIME() を通さないと UTC の日付とずれる"""
    sql = (
        "WITH t(ts) AS (VALUES ('2024-02-29 00:00:00'), ('2024-02-29 23:59:59.5'), ('2024-03-01 00:00:00'))"
        " SELECT COUNT(*) FROM t WHERE ts >= DATE('2024-02-29 13:00:00') AND ts < DATE('2024-02-29 13:00:00', '+1 day')"
    )
    assert run("sqlite", sql) == [(2,)]
    offset = (
        "WITH t(ts) AS (VALUES ('2024-03-01 08:45:07+09:00'))"
        " SELECT ts >= DATE('2024-02-29') AND ts < DATE('2024-02-29', '+1 day'),"
        " DATETIME(ts) >= DATE('2024-02-29') AND DATETIME(ts) < DATE('2024-02-29', '+1 day') FROM t"
    )
    assert run("sqlite", offset) == [(0, 1)]
