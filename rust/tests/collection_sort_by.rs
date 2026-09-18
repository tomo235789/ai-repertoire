//! カード collection-sort-by（slice::sort_by_key）の Contract を検証するテスト

use itertools::Itertools;
use std::cmp::Reverse;

/// 複数キーはタプルで、左から順に比較する
#[test]
fn sorts_by_tuple_keys() {
    let mut rows = vec![("b", 2), ("a", 9), ("b", 1)];
    rows.sort_by_key(|r| (r.0, r.1));
    assert_eq!(rows, vec![("a", 9), ("b", 1), ("b", 2)]);
}

/// 安定ソートで、キーが等しい要素は元の相対順を保つ
#[test]
fn is_stable() {
    let mut rows: Vec<(i32, i32)> = (0..100).map(|i| (i % 3, i)).collect();
    rows.sort_by_key(|r| r.0);
    let ordered = rows.windows(2).all(|w| w[0].0 < w[1].0 || (w[0].0 == w[1].0 && w[0].1 < w[1].1));
    assert!(ordered);
}

/// その場で並べ替え、即時評価で戻った時点で完了している
#[test]
fn sorts_in_place_eagerly() {
    let mut xs = vec![3, 1, 2];
    xs.sort_by_key(|x| *x);
    assert_eq!(xs, vec![1, 2, 3]);
}

/// キー関数は複数回呼ばれうる（回数は契約ではない）。sort_by_cached_key は各要素につき最大 1 回
#[test]
fn key_call_counts() {
    let mut xs: Vec<i32> = (0..50).rev().collect();
    xs.sort_by_key(|x| *x);
    let mut cached_calls = 0;
    let mut ys: Vec<i32> = (0..50).rev().collect();
    ys.sort_by_cached_key(|x| {
        cached_calls += 1;
        *x
    });
    assert!(cached_calls <= 50);
    assert_eq!(ys, (0..50).collect::<Vec<i32>>());
    assert_eq!(xs, ys);
}

/// Option は None が先頭、&str はバイト順
#[test]
fn ord_semantics_of_common_keys() {
    let mut opts = vec![Some(2), None, Some(1)];
    opts.sort_by_key(|x| *x);
    assert_eq!(opts, vec![None, Some(1), Some(2)]);
    let mut strs = vec!["b", "B", "a", "A"];
    strs.sort_by_key(|s| *s);
    assert_eq!(strs, vec!["A", "B", "a", "b"]);
}

/// 空スライスでも panic しない
#[test]
fn empty_slice_is_fine() {
    let mut xs: Vec<i32> = vec![];
    xs.sort_by_key(|x| *x);
    assert!(xs.is_empty());
}

/// 非破壊なら sorted_by_key、降順は Reverse、f64 は total_cmp
#[test]
fn alternatives() {
    let rows = [("b", 2), ("a", 9)];
    let sorted: Vec<(&str, i32)> = rows.iter().copied().sorted_by_key(|r| r.0).collect();
    assert_eq!(sorted, vec![("a", 9), ("b", 2)]);
    assert_eq!(rows, [("b", 2), ("a", 9)]);
    let mut desc = vec![1, 3, 2];
    desc.sort_by_key(|x| Reverse(*x));
    assert_eq!(desc, vec![3, 2, 1]);
    let mut fs = vec![2.5f64, -1.0, f64::NAN, 0.0];
    fs.sort_by(|a, b| a.total_cmp(b));
    assert_eq!(&fs[..3], &[-1.0, 0.0, 2.5]);
    assert!(fs[3].is_nan());
}
