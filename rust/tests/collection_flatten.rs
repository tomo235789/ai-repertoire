//! カード collection-flatten（Iterator::flatten）の Contract を検証するテスト

/// 外側・内側とも順序を保って 1 段開く
#[test]
fn flattens_one_level_in_order() {
    let nested = vec![vec![1, 2], vec![], vec![3]];
    let flat: Vec<i32> = nested.into_iter().flatten().collect();
    assert_eq!(flat, vec![1, 2, 3]);
}

/// iter() なら内側への参照、into_iter() なら所有権が移る
#[test]
fn borrows_or_takes_ownership() {
    let nested = vec![vec![1, 2], vec![3]];
    let refs: Vec<&i32> = nested.iter().flatten().collect();
    assert!(std::ptr::eq(refs[2], &nested[1][0]));
    assert_eq!(nested, vec![vec![1, 2], vec![3]]);
    let owned: Vec<i32> = nested.into_iter().flatten().collect();
    assert_eq!(owned, vec![1, 2, 3]);
}

/// 遅延評価で、取り出した分だけ外側を読み進める
#[test]
fn is_lazy() {
    let mut outer_calls = 0;
    let mut it = (0..3).map(|i| {
        outer_calls += 1;
        vec![i; 2]
    }).flatten();
    assert_eq!(it.next(), Some(0));
    assert_eq!(it.next(), Some(0));
    drop(it);
    assert_eq!(outer_calls, 1);
}

/// 開くのは 1 段だけ。2 段は flatten を重ねる
#[test]
fn only_one_level() {
    let deep = vec![vec![vec![1], vec![2]], vec![vec![3]]];
    let one: Vec<&Vec<i32>> = deep.iter().flatten().collect();
    assert_eq!(one, vec![&vec![1], &vec![2], &vec![3]]);
    let two: Vec<i32> = deep.into_iter().flatten().flatten().collect();
    assert_eq!(two, vec![1, 2, 3]);
}

/// Option / Result は Some / Ok だけが残る
#[test]
fn option_and_result_keep_only_some_and_ok() {
    let some: Vec<i32> = vec![Some(1), None, Some(3)].into_iter().flatten().collect();
    assert_eq!(some, vec![1, 3]);
    let results: Vec<Result<i32, &str>> = vec![Ok(1), Err("x"), Ok(3)];
    let ok: Vec<i32> = results.into_iter().flatten().collect();
    assert_eq!(ok, vec![1, 3]);
}

/// 空の入力、または空の内側だけなら何も返さない
#[test]
fn empty_inputs_yield_nothing() {
    let empty: Vec<Vec<i32>> = vec![];
    assert_eq!(empty.into_iter().flatten().count(), 0);
    let only_empties: Vec<Vec<i32>> = vec![vec![], vec![]];
    assert_eq!(only_empties.into_iter().flatten().collect::<Vec<i32>>(), Vec::<i32>::new());
}

/// flat_map は変換しながら 1 段開く
#[test]
fn flat_map_transforms_then_flattens() {
    let chars: Vec<char> = ["ab", "cd"].iter().flat_map(|s| s.chars()).collect();
    assert_eq!(chars, vec!['a', 'b', 'c', 'd']);
}
