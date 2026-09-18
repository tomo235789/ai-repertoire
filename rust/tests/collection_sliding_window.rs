//! カード collection-sliding-window（slice::windows）の Contract を検証するテスト

use itertools::Itertools;

/// 順序を保ち、1 つずつずれた窓を返す
#[test]
fn slides_one_step_in_order() {
    let xs = [1, 2, 3, 4, 5];
    let windows: Vec<&[i32]> = xs.windows(3).collect();
    assert_eq!(windows, vec![&[1, 2, 3][..], &[2, 3, 4][..], &[3, 4, 5][..]]);
}

/// 入力を変更せず、各窓は元のスライスの一部を借用している
#[test]
fn borrows_without_copying() {
    let xs = vec![10, 20, 30];
    let windows: Vec<&[i32]> = xs.windows(2).collect();
    assert!(std::ptr::eq(windows[1].as_ptr(), &xs[1]));
    assert_eq!(xs, vec![10, 20, 30]);
}

/// 遅延評価で、ExactSizeIterator / DoubleEndedIterator として使える
#[test]
fn is_exact_size_and_double_ended() {
    let xs = [1, 2, 3, 4, 5];
    let mut it = xs.windows(3);
    assert_eq!(it.len(), 3);
    assert_eq!(it.next(), Some(&[1, 2, 3][..]));
    assert_eq!(it.len(), 2);
    let rev: Vec<&[i32]> = xs.windows(2).rev().collect();
    assert_eq!(rev, vec![&[4, 5][..], &[3, 4][..], &[2, 3][..], &[1, 2][..]]);
}

/// 窓の数は len - size + 1 で、末尾の短い窓は作らない
#[test]
fn drops_partial_tail() {
    let xs = [1, 2, 3, 4, 5];
    assert_eq!(xs.windows(5).collect::<Vec<_>>(), vec![&[1, 2, 3, 4, 5][..]]);
    assert_eq!(xs.windows(4).count(), 2);
    assert!(xs.windows(4).all(|w| w.len() == 4));
}

/// スライス長が size 未満、または空なら何も返さない
#[test]
fn shorter_than_size_yields_nothing() {
    assert_eq!([1, 2].windows(3).count(), 0);
    let empty: [i32; 0] = [];
    assert_eq!(empty.windows(1).count(), 0);
}

/// size == 0 は panic する
#[test]
#[should_panic(expected = "window size must be non-zero")]
fn zero_size_panics() {
    let xs = [1, 2, 3];
    let _ = xs.windows(0);
}

/// step は step_by で、タプルで受けるなら tuple_windows
#[test]
fn step_by_and_tuple_windows() {
    let xs = [1, 2, 3, 4, 5];
    let stepped: Vec<&[i32]> = xs.windows(3).step_by(2).collect();
    assert_eq!(stepped, vec![&[1, 2, 3][..], &[3, 4, 5][..]]);
    let pairs: Vec<(i32, i32)> = xs.iter().copied().tuple_windows().collect();
    assert_eq!(pairs, vec![(1, 2), (2, 3), (3, 4), (4, 5)]);
}

/// 移動平均の例
#[test]
fn moving_average() {
    let avg: Vec<f64> = [1.0, 2.0, 3.0, 4.0].windows(2).map(|w| w.iter().sum::<f64>() / 2.0).collect();
    assert_eq!(avg, vec![1.5, 2.5, 3.5]);
}
