//! カード collection-zip（Iterator::zip）の Contract を検証するテスト

use itertools::{EitherOrBoth, Itertools};

/// 順序を保ち、同じ位置どうしをタプルにする
#[test]
fn pairs_in_order() {
    let labels = ["a", "b", "c"];
    let values = [1, 2, 3];
    let pairs: Vec<(&str, i32)> = labels.into_iter().zip(values).collect();
    assert_eq!(pairs, vec![("a", 1), ("b", 2), ("c", 3)]);
}

/// other は IntoIterator なら何でもよく、iter() なら参照になる
#[test]
fn accepts_any_into_iterator() {
    let xs = vec![1, 2];
    let ys = vec![10, 20];
    let refs: Vec<(&i32, &i32)> = xs.iter().zip(&ys).collect();
    assert!(std::ptr::eq(refs[0].0, &xs[0]));
    assert_eq!(refs, vec![(&1, &10), (&2, &20)]);
    let with_range: Vec<(i32, i32)> = xs.into_iter().zip(0..).collect();
    assert_eq!(with_range, vec![(1, 0), (2, 1)]);
}

/// 遅延評価で、取り出した分だけ入力を読み進める
#[test]
fn is_lazy() {
    let mut calls = 0;
    let mut z = (0..).map(|i| {
        calls += 1;
        i
    }).zip([1, 2, 3]);
    assert_eq!(z.next(), Some((0, 1)));
    drop(z);
    assert_eq!(calls, 1);
}

/// 長さは最も短い入力に合わせて打ち切る
#[test]
fn truncates_to_shortest() {
    let pairs: Vec<(char, i32)> = ['a', 'b', 'c'].into_iter().zip([1, 2]).collect();
    assert_eq!(pairs, vec![('a', 1), ('b', 2)]);
}

/// どちらかが空なら何も返さない
#[test]
fn empty_side_yields_nothing() {
    let pairs: Vec<(i32, i32)> = std::iter::empty::<i32>().zip([1, 2]).collect();
    assert!(pairs.is_empty());
    let pairs: Vec<(i32, i32)> = [1, 2].into_iter().zip(std::iter::empty::<i32>()).collect();
    assert!(pairs.is_empty());
}

/// 一般のイテレータでは、後ろ側が尽きたとき先頭側から 1 要素余分に消費される
#[test]
fn general_iterator_consumes_one_extra_from_first() {
    let mut chars = "abc".chars();
    let pairs: Vec<(char, i32)> = chars.by_ref().zip([1, 2]).collect();
    assert_eq!(pairs.len(), 2);
    assert_eq!(chars.collect::<String>(), "");
}

/// 余った要素は消費されるとは限らず、by_ref() で渡した後ろ側の残りは続けて読める
#[test]
fn surplus_on_second_side_remains_readable() {
    let mut nums = [1, 2, 3].into_iter();
    let pairs: Vec<(char, i32)> = "ab".chars().zip(nums.by_ref()).collect();
    assert_eq!(pairs, vec![('a', 1), ('b', 2)]);
    assert_eq!(nums.collect::<Vec<_>>(), vec![3]);
}

/// zip_longest は最も長い入力に合わせ、zip_eq は不一致で panic する
#[test]
fn zip_longest_fills_with_either_or_both() {
    let all: Vec<EitherOrBoth<char, i32>> = ['a', 'b', 'c'].into_iter().zip_longest([1, 2]).collect();
    assert_eq!(all, vec![EitherOrBoth::Both('a', 1), EitherOrBoth::Both('b', 2), EitherOrBoth::Left('c')]);
}

/// zip_eq は長さが違うと panic する
#[test]
#[should_panic(expected = "zip_eq() reached end of one iterator before the other")]
fn zip_eq_panics_on_length_mismatch() {
    let _ = ['a', 'b', 'c'].into_iter().zip_eq([1, 2]).count();
}

/// unzip は逆操作
#[test]
fn unzip_reverses() {
    let pairs = vec![("a", 1), ("b", 2)];
    let (labels, values): (Vec<&str>, Vec<i32>) = pairs.into_iter().unzip();
    assert_eq!(labels, vec!["a", "b"]);
    assert_eq!(values, vec![1, 2]);
}
