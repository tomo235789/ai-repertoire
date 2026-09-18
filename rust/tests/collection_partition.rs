//! カード collection-partition（Iterator::partition）の Contract を検証するテスト

use itertools::{Either, Itertools};
use std::collections::HashSet;

/// 順序を保ち、(真, 偽) の順で返す
#[test]
fn splits_in_order_truthy_first() {
    let (even, odd): (Vec<i32>, Vec<i32>) = (1..=5).partition(|n| n % 2 == 0);
    assert_eq!(even, vec![2, 4]);
    assert_eq!(odd, vec![1, 3, 5]);
}

/// iter() なら参照、into_iter() なら所有権が移る
#[test]
fn borrows_or_takes_ownership() {
    let xs = vec![1, 2, 3];
    let (big, small): (Vec<&i32>, Vec<&i32>) = xs.iter().partition(|n| **n > 1);
    assert!(std::ptr::eq(big[0], &xs[1]));
    assert_eq!(small, vec![&1]);
    let (big, small): (Vec<i32>, Vec<i32>) = xs.into_iter().partition(|n| *n > 1);
    assert_eq!((big, small), (vec![2, 3], vec![1]));
}

/// 即時評価で、述語は各要素につき 1 回ずつ先頭から順に呼ばれる
#[test]
fn eager_and_calls_predicate_once_in_order() {
    let mut seen = vec![];
    let (t, f): (Vec<i32>, Vec<i32>) = [3, 1, 2].into_iter().partition(|n| {
        seen.push(*n);
        *n > 1
    });
    assert_eq!(seen, vec![3, 1, 2]);
    assert_eq!(t, vec![3, 2]);
    assert_eq!(f, vec![1]);
}

/// 返り値は Default + Extend な任意のコレクション
#[test]
fn any_extendable_collection() {
    let (upper, lower): (String, String) = "aBcD".chars().partition(|c| c.is_uppercase());
    assert_eq!(upper, "BD");
    assert_eq!(lower, "ac");
    let (even, odd): (HashSet<i32>, HashSet<i32>) = (1..=5).partition(|n| n % 2 == 0);
    assert_eq!(even, HashSet::from([2, 4]));
    assert_eq!(odd, HashSet::from([1, 3, 5]));
}

/// 空の入力は空のコレクション 2 つ
#[test]
fn empty_input_gives_two_empties() {
    let (t, f): (Vec<i32>, Vec<i32>) = std::iter::empty::<i32>().partition(|n| *n > 0);
    assert!(t.is_empty());
    assert!(f.is_empty());
}

/// partition_map は振り分けながら別々の型に変換できる
#[test]
fn partition_map_converts_each_side() {
    let (oks, errs): (Vec<i32>, Vec<String>) = ["1", "x", "3"]
        .into_iter()
        .partition_map(|s| match s.parse::<i32>() {
            Ok(n) => Either::Left(n),
            Err(e) => Either::Right(e.to_string()),
        });
    assert_eq!(oks, vec![1, 3]);
    assert_eq!(errs.len(), 1);
}
