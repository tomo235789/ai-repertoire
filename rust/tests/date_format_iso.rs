//! date-format-iso: chrono の DateTime::to_rfc3339 の契約を検証する

use chrono::{DateTime, Duration, FixedOffset, Local, NaiveDate, SecondsFormat, TimeZone, Utc};

fn utc() -> DateTime<Utc> {
    Utc.with_ymd_and_hms(2024, 2, 29, 13, 45, 7).unwrap()
}

fn jst() -> DateTime<FixedOffset> {
    FixedOffset::east_opt(9 * 3600).unwrap().with_ymd_and_hms(2024, 2, 29, 13, 45, 7).unwrap()
}

#[test]
fn formats_with_offset_of_the_value() {
    // 値が持つオフセットを付ける。UTC は +00:00 で Z にはならない
    assert_eq!(utc().to_rfc3339(), "2024-02-29T13:45:07+00:00");
    assert_eq!(jst().to_rfc3339(), "2024-02-29T13:45:07+09:00");
    let west = FixedOffset::west_opt(5 * 3600 + 1800).unwrap();
    assert_eq!(west.with_ymd_and_hms(2024, 2, 29, 1, 2, 3).unwrap().to_rfc3339(), "2024-02-29T01:02:03-05:30");
    let local = Local::now();
    assert!(local.to_rfc3339().ends_with(&local.offset().to_string()));
}

#[test]
fn default_omits_zero_subseconds_and_trims_trailing_zeros() {
    // 秒未満が 0 なら秒まで、それ以外は末尾の 0 を省いてナノ秒まで
    assert_eq!((utc() + Duration::nanoseconds(123_456_789)).to_rfc3339(), "2024-02-29T13:45:07.123456789+00:00");
    assert_eq!((utc() + Duration::milliseconds(123)).to_rfc3339(), "2024-02-29T13:45:07.123+00:00");
}

#[test]
fn opts_fix_digits_and_use_z() {
    // to_rfc3339_opts で桁を固定し、use_z はオフセット 0 のときだけ Z にする
    assert_eq!(utc().to_rfc3339_opts(SecondsFormat::Secs, true), "2024-02-29T13:45:07Z");
    assert_eq!(utc().to_rfc3339_opts(SecondsFormat::Secs, false), "2024-02-29T13:45:07+00:00");
    assert_eq!(utc().to_rfc3339_opts(SecondsFormat::Millis, true), "2024-02-29T13:45:07.000Z");
    assert_eq!(utc().to_rfc3339_opts(SecondsFormat::Nanos, true), "2024-02-29T13:45:07.000000000Z");
    assert_eq!(utc().to_rfc3339_opts(SecondsFormat::AutoSi, true), "2024-02-29T13:45:07Z");
    let ms = utc() + Duration::milliseconds(999);
    assert_eq!(ms.to_rfc3339_opts(SecondsFormat::AutoSi, true), "2024-02-29T13:45:07.999Z");
    assert_eq!(jst().to_rfc3339_opts(SecondsFormat::Secs, true), "2024-02-29T13:45:07+09:00");
    let zero_offset = FixedOffset::east_opt(0).unwrap().with_ymd_and_hms(2024, 2, 29, 0, 0, 0).unwrap();
    assert_eq!(zero_offset.to_rfc3339_opts(SecondsFormat::Secs, true), "2024-02-29T00:00:00Z");
}

#[test]
fn truncates_when_dropping_digits() {
    // 桁を落とすときは切り捨て
    let us = utc() + Duration::microseconds(999_999);
    assert_eq!(us.to_rfc3339_opts(SecondsFormat::Millis, true), "2024-02-29T13:45:07.999Z");
    let ns = utc() + Duration::nanoseconds(123_456_789);
    assert_eq!(ns.to_rfc3339_opts(SecondsFormat::Millis, true), "2024-02-29T13:45:07.123Z");
}

#[test]
fn year_is_zero_padded_and_signed_outside_four_digits() {
    // 年は 4 桁ゼロ埋め。5 桁以上と負の年は符号付き
    assert_eq!(Utc.with_ymd_and_hms(1, 1, 1, 0, 0, 0).unwrap().to_rfc3339(), "0001-01-01T00:00:00+00:00");
    assert_eq!(Utc.with_ymd_and_hms(12345, 1, 1, 0, 0, 0).unwrap().to_rfc3339(), "+12345-01-01T00:00:00+00:00");
    assert_eq!(Utc.with_ymd_and_hms(-1, 1, 1, 0, 0, 0).unwrap().to_rfc3339(), "-0001-01-01T00:00:00+00:00");
}

#[test]
fn naive_datetime_has_no_offset() {
    // NaiveDateTime は Display が空白区切り、Debug が T 区切り。%+ はエラー
    let naive = NaiveDate::from_ymd_opt(2024, 2, 29).unwrap().and_hms_opt(13, 45, 7).unwrap();
    assert_eq!(naive.to_string(), "2024-02-29 13:45:07");
    assert_eq!(format!("{:?}", naive), "2024-02-29T13:45:07");
    assert_eq!(naive.format("%Y-%m-%dT%H:%M:%S").to_string(), "2024-02-29T13:45:07");
    assert_eq!(naive.and_utc().to_rfc3339(), "2024-02-29T13:45:07+00:00");
    let result = std::panic::catch_unwind(|| naive.format("%+").to_string());
    assert!(result.is_err());
}

#[test]
fn parse_from_rfc3339_round_trips() {
    // parse_from_rfc3339 で逆変換。Z は +00:00、オフセット無しは Err
    let parsed = DateTime::parse_from_rfc3339("2024-02-29T13:45:07+09:00").unwrap();
    assert_eq!(parsed, jst());
    assert_eq!(parsed.offset(), jst().offset());
    let zulu = DateTime::parse_from_rfc3339("2024-02-29T04:45:07Z").unwrap();
    assert_eq!(zulu, jst());
    assert_eq!(zulu.offset(), &FixedOffset::east_opt(0).unwrap());
    assert!(DateTime::parse_from_rfc3339("2024-02-29T13:45:07").is_err());
    assert!(DateTime::parse_from_rfc3339("2024-02-29").is_err());
    assert_eq!(DateTime::parse_from_rfc3339(&jst().to_rfc3339()).unwrap(), jst());
    let as_utc: DateTime<Utc> = "2024-02-29T13:45:07+09:00".parse().unwrap();
    assert_eq!(as_utc.to_rfc3339(), "2024-02-29T04:45:07+00:00");
}

#[test]
fn does_not_mutate_input() {
    // &self なので入力はそのまま
    let dt = jst();
    let _ = dt.to_rfc3339();
    assert_eq!(dt, jst());
}

#[test]
fn format_display_debug_and_utc_conversion() {
    // %+ は to_rfc3339 と同じ。Display は空白区切り、Debug は T 区切り
    assert_eq!(jst().format("%+").to_string(), "2024-02-29T13:45:07+09:00");
    assert_eq!(jst().format("%Y-%m-%dT%H:%M:%S%:z").to_string(), "2024-02-29T13:45:07+09:00");
    assert_eq!(jst().format("%z").to_string(), "+0900");
    assert_eq!(jst().to_string(), "2024-02-29 13:45:07 +09:00");
    assert_eq!(format!("{:?}", jst()), "2024-02-29T13:45:07+09:00");
    assert_eq!(jst().with_timezone(&Utc).to_rfc3339_opts(SecondsFormat::Secs, true), "2024-02-29T04:45:07Z");
    assert_eq!(jst().date_naive().to_string(), "2024-02-29");
}

#[test]
fn leap_second_is_printed_as_60() {
    // うるう秒は 23:59:60 と出力される
    let leap = NaiveDate::from_ymd_opt(2016, 12, 31).unwrap().and_hms_milli_opt(23, 59, 59, 1_500).unwrap().and_utc();
    assert_eq!(leap.to_rfc3339_opts(SecondsFormat::Secs, true), "2016-12-31T23:59:60Z");
}
