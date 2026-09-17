//! date-add-days: chrono の DateTime::checked_add_days の契約を検証する

use chrono::{DateTime, Days, Duration, FixedOffset, Months, NaiveDate, TimeZone, Utc};

fn base() -> DateTime<Utc> {
    Utc.with_ymd_and_hms(2024, 2, 29, 13, 45, 7).unwrap()
}

#[test]
fn returns_new_value_without_mutating_input() {
    // 入力は変わらず新しい値を Some で返す。0 日は同じ値
    let d = base();
    let next = d.checked_add_days(Days::new(1));
    assert_eq!(next, Some(Utc.with_ymd_and_hms(2024, 3, 1, 13, 45, 7).unwrap()));
    assert_eq!(d, base());
    assert_eq!(d.checked_add_days(Days::new(0)), Some(d));
}

#[test]
fn carries_over_month_year_and_leap_day() {
    // 月末・年末・うるう年の繰り越しはカレンダーどおり
    assert_eq!(base().checked_add_days(Days::new(1)).unwrap().to_rfc3339(), "2024-03-01T13:45:07+00:00");
    assert_eq!(base().checked_add_days(Days::new(365)).unwrap().to_rfc3339(), "2025-02-28T13:45:07+00:00");
    assert_eq!(base().checked_sub_days(Days::new(1)).unwrap().to_rfc3339(), "2024-02-28T13:45:07+00:00");
    assert_eq!(base().checked_sub_days(Days::new(60)).unwrap().to_rfc3339(), "2023-12-31T13:45:07+00:00");
}

#[test]
fn keeps_time_and_offset_and_matches_duration_without_dst() {
    // 時刻とオフセットは保たれ、FixedOffset / Utc では経過時間は 24 時間 × 日数で Duration と同じ
    let jst = FixedOffset::east_opt(9 * 3600).unwrap();
    let d = jst.with_ymd_and_hms(2024, 2, 29, 23, 30, 0).unwrap();
    let next = d.checked_add_days(Days::new(1)).unwrap();
    assert_eq!(next.to_rfc3339(), "2024-03-01T23:30:00+09:00");
    assert_eq!(next.time(), d.time());
    assert_eq!(next.offset(), d.offset());
    assert_eq!((next - d).num_hours(), 24);
    assert_eq!(next, d + Duration::days(1));
    assert_eq!(base().checked_add_days(Days::new(3)).unwrap(), base() + Duration::days(3));
}

#[test]
fn days_is_unsigned_so_subtraction_uses_checked_sub_days() {
    // Days は u64。負数は変換できないので減算は checked_sub_days
    assert!(u64::try_from(-1_i64).is_err());
    assert_eq!(base().checked_sub_days(Days::new(1)), Some(base() - Duration::days(1)));
}

#[test]
fn out_of_range_returns_none() {
    // 範囲外は None で panic しない
    assert_eq!(DateTime::<Utc>::MAX_UTC.checked_add_days(Days::new(1)), None);
    assert_eq!(DateTime::<Utc>::MIN_UTC.checked_sub_days(Days::new(1)), None);
    assert_eq!(base().checked_add_days(Days::new(u64::MAX)), None);
    assert_eq!(base().checked_add_days(Days::new(1_000_000_000)), None);
    assert_eq!(NaiveDate::MAX.checked_add_days(Days::new(1)), None);
}

#[test]
fn naive_date_and_naive_datetime_have_same_api() {
    // NaiveDate / NaiveDateTime にも同じメソッドがある
    let nd = NaiveDate::from_ymd_opt(2024, 2, 29).unwrap();
    assert_eq!(nd.checked_add_days(Days::new(1)), NaiveDate::from_ymd_opt(2024, 3, 1));
    assert_eq!(nd.checked_add_days(Days::new(365)), NaiveDate::from_ymd_opt(2025, 2, 28));
    assert_eq!(nd.checked_sub_days(Days::new(1)), NaiveDate::from_ymd_opt(2024, 2, 28));
    let ndt = nd.and_hms_opt(13, 45, 7).unwrap();
    assert_eq!(ndt.checked_add_days(Days::new(1)), NaiveDate::from_ymd_opt(2024, 3, 1).unwrap().and_hms_opt(13, 45, 7));
}

#[test]
#[should_panic(expected = "overflowed")]
fn duration_addition_panics_out_of_range() {
    // + Duration は範囲外で panic する（checked_add_signed なら None）
    assert_eq!(DateTime::<Utc>::MAX_UTC.checked_add_signed(Duration::days(1)), None);
    let _ = DateTime::<Utc>::MAX_UTC + Duration::days(1);
}

#[test]
#[should_panic(expected = "out of bounds")]
fn duration_days_panics_on_huge_value() {
    // Duration::days は大きすぎる値で panic する（try_days なら None）
    assert_eq!(Duration::try_days(i64::MAX), None);
    let _ = Duration::days(i64::MAX);
}

#[test]
fn hours_and_naive_date_truncation() {
    // 時間単位は Duration::hours。NaiveDate + Duration は日未満を切り捨てる
    assert_eq!((base() + Duration::hours(36)).to_rfc3339(), "2024-03-02T01:45:07+00:00");
    let nd = NaiveDate::from_ymd_opt(2024, 2, 29).unwrap();
    assert_eq!(nd + Duration::hours(23), nd);
    assert_eq!(nd + Duration::hours(36), NaiveDate::from_ymd_opt(2024, 3, 1).unwrap());
    assert_eq!(nd.succ_opt(), NaiveDate::from_ymd_opt(2024, 3, 1));
    assert_eq!((base() + Duration::weeks(1)).to_rfc3339(), "2024-03-07T13:45:07+00:00");
}

#[test]
fn months_clamp_to_end_of_month() {
    // checked_add_months は月末を月の最終日にクランプする
    let jan31 = NaiveDate::from_ymd_opt(2024, 1, 31).unwrap();
    assert_eq!(jan31.checked_add_months(Months::new(1)), NaiveDate::from_ymd_opt(2024, 2, 29));
    let feb29 = NaiveDate::from_ymd_opt(2024, 2, 29).unwrap();
    assert_eq!(feb29.checked_add_months(Months::new(12)), NaiveDate::from_ymd_opt(2025, 2, 28));
    let utc_jan31 = Utc.with_ymd_and_hms(2024, 1, 31, 10, 0, 0).unwrap();
    assert_eq!(utc_jan31.checked_add_months(Months::new(1)).unwrap().to_rfc3339(), "2024-02-29T10:00:00+00:00");
}
