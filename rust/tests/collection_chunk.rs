//! カード collection-chunk（slice::chunks）の Contract を検証するテスト

/// 順序を保ったまま chunk_size ごとに分割し、最後は短くなる
#[test]
fn splits_in_order_with_short_tail() {
    let xs = [1, 2, 3, 4, 5];
    let chunks: Vec<&[i32]> = xs.chunks(2).collect();
    assert_eq!(chunks, vec![&[1, 2][..], &[3, 4][..], &[5][..]]);
}

/// 入力を変更せず、各部分スライスは元のスライスの一部を借用している
#[test]
fn borrows_without_copying() {
    let xs = vec![10, 20, 30];
    let chunks: Vec<&[i32]> = xs.chunks(2).collect();
    assert!(std::ptr::eq(chunks[0].as_ptr(), xs.as_ptr()));
    assert!(std::ptr::eq(chunks[1].as_ptr(), &xs[2]));
    assert_eq!(xs, vec![10, 20, 30]);
}

/// 遅延評価で、ExactSizeIterator / DoubleEndedIterator として使える
#[test]
fn is_exact_size_and_double_ended() {
    let xs = [1, 2, 3, 4, 5];
    let mut it = xs.chunks(2);
    assert_eq!(it.len(), 3);
    assert_eq!(it.next(), Some(&[1, 2][..]));
    assert_eq!(it.len(), 2);
    let rev: Vec<&[i32]> = xs.chunks(2).rev().collect();
    assert_eq!(rev, vec![&[5][..], &[3, 4][..], &[1, 2][..]]);
}

/// chunk_size がスライス長を超えると全体が 1 つの部分スライスになる
#[test]
fn larger_size_returns_whole_slice() {
    let xs = [1, 2, 3];
    let chunks: Vec<&[i32]> = xs.chunks(10).collect();
    assert_eq!(chunks, vec![&[1, 2, 3][..]]);
}

/// 空スライスは何も返さない
#[test]
fn empty_slice_yields_nothing() {
    let xs: [i32; 0] = [];
    assert_eq!(xs.chunks(3).count(), 0);
    assert_eq!(xs.chunks(3).collect::<Vec<_>>(), Vec::<&[i32]>::new());
}

/// chunk_size == 0 は panic する
#[test]
#[should_panic(expected = "chunk size must be non-zero")]
fn zero_size_panics() {
    let xs = [1, 2, 3];
    let _ = xs.chunks(0);
}

/// Vec<Vec<T>> にするなら to_vec で所有権を取る
#[test]
fn to_vec_makes_owned_chunks() {
    let xs = vec![1, 2, 3, 4, 5];
    let owned: Vec<Vec<i32>> = xs.chunks(2).map(<[i32]>::to_vec).collect();
    assert_eq!(owned, vec![vec![1, 2], vec![3, 4], vec![5]]);
}

/// chunks_exact は端数を捨て、remainder で取り出せる
#[test]
fn chunks_exact_drops_remainder() {
    let xs = [1, 2, 3, 4, 5];
    let it = xs.chunks_exact(2);
    assert_eq!(it.remainder(), &[5]);
    assert_eq!(it.collect::<Vec<_>>(), vec![&[1, 2][..], &[3, 4][..]]);
}
