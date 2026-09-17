//! カード collection-dedup-by-key（Itertools::unique_by）の Contract を検証するテスト

use itertools::Itertools;

/// 順序を保ち、同じキーの要素は最初に出現したものを残す
#[test]
fn keeps_first_occurrence_in_order() {
    let users = vec![(1, "a"), (2, "b"), (1, "c")];
    let uniq: Vec<&(i32, &str)> = users.iter().unique_by(|u| u.0).collect();
    assert_eq!(uniq, vec![&(1, "a"), &(2, "b")]);
}

/// 入力を変更せず、iter() なら参照、into_iter() なら所有権が移る
#[test]
fn borrows_or_takes_ownership() {
    let names = vec!["apple".to_string(), "avocado".to_string(), "banana".to_string()];
    let refs: Vec<&String> = names.iter().unique_by(|s| s.chars().next()).collect();
    assert!(std::ptr::eq(refs[0], &names[0]));
    assert_eq!(names.len(), 3);
    let owned: Vec<String> = names.into_iter().unique_by(|s| s.len()).collect();
    assert_eq!(owned, vec!["apple", "avocado", "banana"]);
}

/// 遅延評価で、取り出した分だけキー関数が呼ばれる
#[test]
fn is_lazy() {
    let mut calls = 0;
    let mut it = [1, 1, 2].iter().unique_by(|x| {
        calls += 1;
        **x
    });
    assert_eq!(it.next(), Some(&1));
    drop(it);
    assert_eq!(calls, 1);
}

/// キー関数は各要素につきちょうど 1 回、先頭から順に呼ばれる
#[test]
fn calls_key_once_per_element_in_order() {
    let mut seen = vec![];
    let _: Vec<&i32> = [3, 1, 3, 2]
        .iter()
        .unique_by(|x| {
            seen.push(**x);
            **x
        })
        .collect();
    assert_eq!(seen, vec![3, 1, 3, 2]);
}

/// キーは == とハッシュで比較され、複合キーはタプルにする
#[test]
fn compares_keys_by_value() {
    let rows = vec![("a", 1, "x"), ("a", 1, "y"), ("a", 2, "z")];
    let uniq: Vec<&(&str, i32, &str)> = rows.iter().unique_by(|r| (r.0.to_string(), r.1)).collect();
    assert_eq!(uniq, vec![&("a", 1, "x"), &("a", 2, "z")]);
}

/// 空の入力は何も返さない
#[test]
fn empty_input_yields_nothing() {
    let xs: Vec<i32> = vec![];
    assert_eq!(xs.iter().unique_by(|x| **x).count(), 0);
}

/// dedup_by は隣接する重複しか消さない（unique_by との違い）
#[test]
fn dedup_by_only_removes_adjacent() {
    let xs = [1, 2, 1];
    let adjacent: Vec<&i32> = xs.iter().dedup_by(|a, b| a == b).collect();
    assert_eq!(adjacent, vec![&1, &2, &1]);
    let all: Vec<&i32> = xs.iter().unique_by(|x| **x).collect();
    assert_eq!(all, vec![&1, &2]);
    let mut v = vec![1, 2, 1];
    v.dedup_by_key(|x| *x);
    assert_eq!(v, vec![1, 2, 1]);
}

/// f64 は to_bits のビット表現をそのままキーにする（値の正規化ではないので 0.0 と -0.0 は別キー）
#[test]
fn f64_key_via_to_bits() {
    let xs = [1.0f64, 2.0, 1.0];
    let uniq: Vec<&f64> = xs.iter().unique_by(|x| x.to_bits()).collect();
    assert_eq!(uniq, vec![&1.0, &2.0]);
    let zeros = [0.0f64, -0.0];
    assert_eq!(zeros.iter().unique_by(|x| x.to_bits()).count(), 2);
}
