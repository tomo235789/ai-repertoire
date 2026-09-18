//! number-clamp: Ord::clamp / f64::clamp の契約を検証する

#[test]
fn clamps_to_bounds_inclusive() {
    // 範囲外は境界値に、範囲内はそのまま。境界値は含む
    assert_eq!(150.clamp(0, 100), 100);
    assert_eq!((-5).clamp(0, 100), 0);
    assert_eq!(42.clamp(0, 100), 42);
    assert_eq!(0.clamp(0, 100), 0);
    assert_eq!(100.clamp(0, 100), 100);
}

#[test]
fn works_for_any_ord_type() {
    // Ord を実装する型なら何でも使え、返り値は 3 引数のいずれか
    assert_eq!(5u8.clamp(1, 3), 3);
    assert_eq!('z'.clamp('a', 'm'), 'm');
    assert_eq!("m".clamp("a", "k"), "k");
    assert_eq!((1, 9).clamp((1, 5), (2, 0)), (1, 9));
    let x = 7;
    assert_eq!(x.clamp(0, 10), x); // 引数は変更されない（Copy）
}

#[test]
#[should_panic(expected = "min > max")]
fn panics_when_min_greater_than_max() {
    // min > max は panic（TypeScript / Python のように max を返さない）
    let _ = 5.clamp(10, 1);
}

#[test]
fn f64_clamp_basic_and_nan_value() {
    // f64 は固有メソッド。x が NaN なら NaN を返す
    assert_eq!(2.5_f64.clamp(0.0, 1.0), 1.0);
    assert_eq!((-1.0_f64).clamp(0.0, 1.0), 0.0);
    assert_eq!(0.5_f64.clamp(0.0, 1.0), 0.5);
    assert!(f64::NAN.clamp(0.0, 1.0).is_nan());
}

#[test]
#[should_panic(expected = "either was NaN")]
fn f64_clamp_panics_on_nan_bound() {
    // 境界が NaN なら panic
    let _ = 0.5_f64.clamp(f64::NAN, 1.0);
}

#[test]
#[should_panic(expected = "min > max")]
fn f64_clamp_panics_when_min_greater_than_max() {
    // f64 でも min > max は panic
    let _ = 0.5_f64.clamp(1.0, 0.0);
}

#[test]
fn f64_clamp_keeps_negative_zero_and_saturates_infinity() {
    // -0.0 は 0.0 に置き換わらず、無限大は境界に収まる
    assert!((-0.0_f64).clamp(0.0, 1.0).is_sign_negative());
    assert_eq!(f64::INFINITY.clamp(0.0, 1.0), 1.0);
    assert_eq!(f64::NEG_INFINITY.clamp(0.0, 1.0), 0.0);
}

#[test]
fn one_sided_alternatives() {
    // 片側だけなら max / min。並べ方で lo > hi のときの結果が変わる
    assert_eq!(150.min(100), 100);
    assert_eq!((-5).max(0), 0);
    assert_eq!(5.min(1).max(10), 10);
    assert_eq!(5.max(10).min(1), 1);
    assert!((0..=100).contains(&42));
}
