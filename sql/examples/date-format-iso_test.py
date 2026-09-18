# カード date-format-iso の Contract を検証するテスト
import re
import sqlite3

import duckdb
import pytest

FMT = "%Y-%m-%dT%H:%M:%SZ"
ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


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


def test_sqlite_formats_text_inputs_as_utc():
    """sqlite: 各種 ISO 形式の入力を UTC の文字列にする。オフセット付きは UTC に変換"""
    sql = (
        f"SELECT STRFTIME('{FMT}', '2024-02-29 13:45:07'), STRFTIME('{FMT}', '2024-02-29T13:45:07'),"
        f" STRFTIME('{FMT}', '2024-02-29'), STRFTIME('{FMT}', '2024-02-29 13:45'),"
        f" STRFTIME('{FMT}', '2024-02-29 13:45:07+09:00'), STRFTIME('{FMT}', '2024-02-29 13:45:07Z'),"
        f" typeof(STRFTIME('{FMT}', '2024-02-29 13:45:07'))"
    )
    assert run("sqlite", sql) == [
        (
            "2024-02-29T13:45:07Z",
            "2024-02-29T13:45:07Z",
            "2024-02-29T00:00:00Z",
            "2024-02-29T13:45:00Z",
            "2024-02-29T04:45:07Z",
            "2024-02-29T13:45:07Z",
            "text",
        )
    ]


def test_sqlite_numeric_inputs():
    """sqlite: 数値はユリウス日、'unixepoch' 付きなら UNIX 秒"""
    sql = (
        f"SELECT STRFTIME('{FMT}', 1709214307, 'unixepoch'), STRFTIME('{FMT}', 2460370)"
    )
    assert run("sqlite", sql) == [("2024-02-29T13:45:07Z", "2024-02-29T12:00:00Z")]


def test_sqlite_invalid_and_null_inputs_give_null():
    """sqlite: 非 ISO 形式・不正な文字列・NULL は NULL。%z も NULL"""
    sql = f"SELECT STRFTIME('{FMT}', '2024/02/29'), STRFTIME('{FMT}', 'not a date'), STRFTIME('{FMT}', NULL), STRFTIME('%Y-%m-%dT%H:%M:%S%z', '2024-02-29 13:45:07')"
    assert run("sqlite", sql) == [(None, None, None, None)]


def test_sqlite_subsecond_truncated_unless_f():
    """sqlite: 秒未満は切り捨て。%f で残る"""
    sql = f"SELECT STRFTIME('{FMT}', '2024-02-29 13:45:07.999'), STRFTIME('%Y-%m-%dT%H:%M:%fZ', '2024-02-29 13:45:07.999')"
    assert run("sqlite", sql) == [("2024-02-29T13:45:07Z", "2024-02-29T13:45:07.999Z")]


def test_sqlite_invalid_day_is_normalized():
    """sqlite: 2024-02-30 は 03-01 に正規化される"""
    assert run("sqlite", f"SELECT STRFTIME('{FMT}', '2024-02-30 13:45:07')") == [
        ("2024-03-01T13:45:07Z",)
    ]


def test_sqlite_now_and_localtime_roundtrip():
    """sqlite: 'now' は書式どおり。'localtime' → 'utc' で元に戻る"""
    rows = run(
        "sqlite",
        f"SELECT STRFTIME('{FMT}', 'now'), STRFTIME('{FMT}', '2024-02-29 13:45:07', 'localtime', 'utc')",
    )
    assert ISO_RE.match(rows[0][0])
    assert rows[0][1] == "2024-02-29T13:45:07Z"


def test_duckdb_argument_order_and_types():
    """duckdb: STRFTIME(ts, fmt)。TIMESTAMP / DATE 型が必要で文字列リテラルはエラー"""
    sql = (
        f"SELECT STRFTIME(TIMESTAMP '2024-02-29 13:45:07', '{FMT}'), STRFTIME(DATE '2024-02-29', '{FMT}'),"
        f" STRFTIME('2024-02-29 13:45:07'::TIMESTAMP, '{FMT}'), STRFTIME(NULL::TIMESTAMP, '{FMT}'),"
        f" typeof(STRFTIME(TIMESTAMP '2024-02-29 13:45:07', '{FMT}')), STRFTIME(TIMESTAMP '2024-02-29 13:45:07', '%Y-%m-%dT%H:%M:%S%z')"
    )
    assert run("duckdb", sql) == [
        (
            "2024-02-29T13:45:07Z",
            "2024-02-29T00:00:00Z",
            "2024-02-29T13:45:07Z",
            None,
            "VARCHAR",
            "2024-02-29T13:45:07+00",
        )
    ]
    with pytest.raises(duckdb.BinderException):
        run("duckdb", f"SELECT STRFTIME('2024-02-29 13:45:07', '{FMT}')")
    varchar_col = (
        "WITH t(s) AS (VALUES ('2024-02-29 13:45:07')) SELECT STRFTIME(s{cast}, '"
        + FMT
        + "') FROM t"
    )
    with pytest.raises(duckdb.BinderException):
        run("duckdb", varchar_col.format(cast=""))
    assert run("duckdb", varchar_col.format(cast="::TIMESTAMP")) == [
        ("2024-02-29T13:45:07Z",)
    ]
    assert run(
        "duckdb", f"SELECT STRFTIME('{FMT}', TIMESTAMP '2024-02-29 13:45:07')"
    ) == [("2024-02-29T13:45:07Z",)]


def test_duckdb_subsecond_and_invalid_day():
    """duckdb: 秒未満は切り捨て（%g / %f で残る）。無い日付は Conversion Error"""
    sql = (
        f"SELECT STRFTIME(TIMESTAMP '2024-02-29 13:45:07.999', '{FMT}'),"
        " STRFTIME(TIMESTAMP '2024-02-29 13:45:07.999', '%Y-%m-%dT%H:%M:%S.%gZ'),"
        " STRFTIME(TIMESTAMP '2024-02-29 13:45:07', '%Y-%m-%dT%H:%M:%S.%fZ')"
    )
    assert run("duckdb", sql) == [
        (
            "2024-02-29T13:45:07Z",
            "2024-02-29T13:45:07.999Z",
            "2024-02-29T13:45:07.000000Z",
        )
    ]
    with pytest.raises(duckdb.ConversionException):
        run("duckdb", f"SELECT STRFTIME('2024-02-30'::TIMESTAMP, '{FMT}')")


def test_duckdb_timestamptz_depends_on_timezone_setting():
    """duckdb: TIMESTAMPTZ は TimeZone 設定のローカル時刻で整形される。AT TIME ZONE 'UTC' で固定"""
    sql = (
        f"SELECT STRFTIME(TIMESTAMPTZ '2024-02-29 13:45:07+09:00', '{FMT}'),"
        f" STRFTIME(TIMESTAMPTZ '2024-02-29 13:45:07+09:00' AT TIME ZONE 'UTC', '{FMT}')"
    )
    assert run_duckdb_with_timezone("UTC", sql) == [
        ("2024-02-29T04:45:07Z", "2024-02-29T04:45:07Z")
    ]
    assert run_duckdb_with_timezone("Asia/Tokyo", sql) == [
        ("2024-02-29T13:45:07Z", "2024-02-29T04:45:07Z")
    ]


def test_roundtrip_alternatives():
    """Alternatives: sqlite は DATETIME、duckdb は ::TIMESTAMP で逆変換できる"""
    assert run("sqlite", "SELECT DATETIME('2024-02-29T13:45:07Z')") == [
        ("2024-02-29 13:45:07",)
    ]
    rows = run(
        "duckdb",
        f"SELECT STRFTIME('2024-02-29T13:45:07Z'::TIMESTAMP, '{FMT}'), (TIMESTAMP '2024-02-29 13:45:07')::VARCHAR",
    )
    assert rows == [("2024-02-29T13:45:07Z", "2024-02-29 13:45:07")]
