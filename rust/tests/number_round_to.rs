//! number-round-to: f64::round と桁指定イディオムの契約を検証する

/// 小数第 digits 位で丸める（負なら 10 の位・100 の位）
fn round_to(x: f64, digits: i32) -> f64 {
    let p = 10_f64.powi(digits);
    (x * p).round() / p
}

#[test]
fn rounds_half_away_from_zero() {
    // .5 は 0 から遠い方へ。偶数丸めではない
    assert_eq!(2.5_f64.round(), 3.0);
    assert_eq!(3.5_f64.round(), 4.0);
    assert_eq!((-2.5_f64).round(), -3.0);
    assert_eq!(0.5_f64.round(), 1.0);
    assert_eq!((-1.5_f64).round(), -2.0);
}

#[test]
fn rounds_to_decimal_places_with_idiom() {
    // 10 の n 乗を掛けて丸めて割ると小数桁を指定できる
    assert_eq!(round_to(3.14159, 2), 3.14);
    assert_eq!(round_to(3.14159, 3), 3.142);
    assert_eq!(round_to(1.2345, 3), 1.235);
    assert_eq!(round_to(2.5, 0), 3.0);
    assert_eq!(round_to(0.1 + 0.2, 1), 0.3);
}

#[test]
fn negative_digits_round_to_tens() {
    // 負の桁数は 10 の位・100 の位で丸める
    assert_eq!(10_f64.powi(-2), 0.01);
    assert_eq!(round_to(1234.5678, -2), 1200.0);
    assert_eq!(round_to(1250.0, -2), 1300.0);
    assert_eq!(round_to(1350.0, -2), 1400.0);
}

#[test]
fn no_floating_point_correction() {
    // 補正はしない。1.005 は 1.0 になり、2.675 は乗算の丸めで 2.68 になる
    assert_eq!(1.005_f64 * 100.0, 100.49999999999999);
    assert_eq!(round_to(1.005, 2), 1.0);
    assert_eq!(2.675_f64 * 100.0, 267.5);
    assert_eq!(round_to(2.675, 2), 2.68);
    assert_eq!(round_to(1.015, 2), 1.01);
}

#[test]
fn nan_infinity_and_negative_zero() {
    // NaN / inf はそのまま。-0.4 は -0.0
    assert!(f64::NAN.round().is_nan());
    assert!(round_to(f64::NAN, 2).is_nan());
    assert_eq!(f64::INFINITY.round(), f64::INFINITY);
    let z = (-0.4_f64).round();
    assert_eq!(z, 0.0);
    assert!(z.is_sign_negative());
}

#[test]
fn overflow_becomes_infinity() {
    // x * p が f64::MAX を超えると inf
    assert_eq!(round_to(f64::MAX, 2), f64::INFINITY);
}

#[test]
fn round_ties_even_alternative() {
    // 偶数丸めが必要なら round_ties_even
    assert_eq!(2.5_f64.round_ties_even(), 2.0);
    assert_eq!(3.5_f64.round_ties_even(), 4.0);
    assert_eq!((-2.5_f64).round_ties_even(), -2.0);
    assert_eq!((-2.5_f64).trunc(), -2.0);
    assert_eq!((-2.5_f64).floor(), -3.0);
    assert_eq!((-2.5_f64).ceil(), -2.0);
}

#[test]
fn format_differs_from_round() {
    // format! は 2 進数の正確な値を偶数丸めするので round と食い違う
    assert_eq!(format!("{:.2}", 2.675_f64), "2.67");
    assert_eq!(format!("{:.0}", 2.5_f64), "2");
    assert_eq!(format!("{:.0}", 3.5_f64), "4");
    assert_eq!(format!("{:.2}", 1.005_f64), "1.00");
    assert_eq!(format!("{:.2}", 0.125_f64), "0.12");
}

#[test]
fn cast_to_integer_saturates() {
    // as による整数変換は範囲外で飽和し、NaN は 0
    assert_eq!(2.5_f64.round() as i64, 3);
    assert_eq!((-2.5_f64).round() as i64, -3);
    assert_eq!(f64::INFINITY as i64, i64::MAX);
    assert_eq!(f64::NAN as i64, 0);
}
