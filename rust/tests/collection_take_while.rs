//! collection-take-while: Iterator::take_while の契約を検証する

use itertools::Itertools;

#[test]
fn takes_prefix_in_order() {
    // 先頭から真の間だけ、順序を保って取り出す
    let v = vec![1, 2, 5, 3, 1];
    let head: Vec<i32> = v.iter().take_while(|&&x| x < 4).copied().collect();
    assert_eq!(head, vec![1, 2]);
}

#[test]
fn lazy_reads_only_what_is_consumed() {
    // 遅延評価。無限イテレータでも打ち切り条件が来れば終わる
    let squares: Vec<u32> = (1..).take_while(|&x| x * x < 30).collect();
    assert_eq!(squares, vec![1, 2, 3, 4, 5]);
}

#[test]
fn iter_borrows_and_into_iter_moves() {
    // iter() は参照、into_iter() は所有権が移る
    let names = vec![String::from("a"), String::from("bb"), String::from("c")];
    let borrowed: Vec<&String> = names.iter().take_while(|s| s.len() == 1).collect();
    assert_eq!(borrowed, vec![&names[0]]);
    let owned: Vec<String> = names.into_iter().take_while(|s| s.len() == 1).collect();
    assert_eq!(owned, vec!["a".to_string()]);
}

#[test]
fn predicate_called_until_first_false() {
    // 述語は最初に偽を返した要素まで呼ばれ、それ以降は呼ばれない
    let v = [1, 2, 5, 3, 1];
    let mut calls = 0;
    let head: Vec<i32> = v
        .iter()
        .take_while(|&&x| {
            calls += 1;
            x < 4
        })
        .copied()
        .collect();
    assert_eq!(head, vec![1, 2]);
    assert_eq!(calls, 3);
}

#[test]
fn first_false_element_is_consumed() {
    // 打ち切りの要素は結果に含まれず、元のイテレータからも消費される
    let v = [1, 2, 5, 3, 1];
    let mut it = v.iter();
    let head: Vec<i32> = it.by_ref().take_while(|&&x| x < 4).copied().collect();
    let rest: Vec<i32> = it.copied().collect();
    assert_eq!(head, vec![1, 2]);
    assert_eq!(rest, vec![3, 1]);
}

#[test]
fn does_not_resume_after_stop() {
    // 一度打ち切ると None を返し続け、後続の真の要素があっても再開しない
    let v = [1, 2, 5, 3, 1];
    let mut it = v.iter().take_while(|&&x| x < 4);
    assert_eq!(it.next(), Some(&1));
    assert_eq!(it.next(), Some(&2));
    assert_eq!(it.next(), None);
    assert_eq!(it.next(), None);
}

#[test]
fn all_true_none_true_and_empty() {
    // すべて真なら全要素、先頭で偽なら空、空入力なら空
    let v = [1, 2, 5, 3, 1];
    let all: Vec<i32> = v.iter().take_while(|_| true).copied().collect();
    let none: Vec<i32> = v.iter().take_while(|_| false).copied().collect();
    let empty: Vec<i32> = Vec::<i32>::new().into_iter().take_while(|_| true).collect();
    assert_eq!(all, vec![1, 2, 5, 3, 1]);
    assert_eq!(none, Vec::<i32>::new());
    assert_eq!(empty, Vec::<i32>::new());
}

#[test]
#[should_panic(expected = "bad element")]
fn predicate_panic_propagates() {
    // 述語の panic はそのまま伝播する
    let _: Vec<i32> = [1, 2, 3]
        .iter()
        .take_while(|&&x| if x == 2 { panic!("bad element") } else { true })
        .copied()
        .collect();
}

#[test]
fn take_while_ref_keeps_first_false_element() {
    // itertools の take_while_ref / peeking_take_while は打ち切りの要素を残す
    let v = [1, 2, 5, 3, 1];
    let mut it = v.iter();
    let head: Vec<i32> = it.take_while_ref(|&&x| x < 4).copied().collect();
    assert_eq!(head, vec![1, 2]);
    assert_eq!(it.copied().collect::<Vec<_>>(), vec![5, 3, 1]);

    let mut it = v.iter().peekable();
    let head: Vec<i32> = it.peeking_take_while(|&&x| x < 4).copied().collect();
    assert_eq!(head, vec![1, 2]);
    assert_eq!(it.copied().collect::<Vec<_>>(), vec![5, 3, 1]);
}

#[test]
fn take_while_inclusive_and_skip_while() {
    // take_while_inclusive は打ち切りの要素まで含め、skip_while は補集合を返す
    let v = [1, 2, 5, 3, 1];
    let inclusive: Vec<i32> = v.iter().take_while_inclusive(|&&x| x < 4).copied().collect();
    assert_eq!(inclusive, vec![1, 2, 5]);
    let rest: Vec<i32> = v.iter().skip_while(|&&x| x < 4).copied().collect();
    assert_eq!(rest, vec![5, 3, 1]);
}

#[test]
fn map_while_and_partition_point() {
    // map_while は Some の間だけ変換して取る。partition_point はソート済みスライスの境界
    let parsed: Vec<i32> = ["1", "2", "x", "4"].iter().map_while(|s| s.parse().ok()).collect();
    assert_eq!(parsed, vec![1, 2]);
    let sorted = [1, 2, 3, 7, 9];
    let n = sorted.partition_point(|&x| x < 4);
    assert_eq!(&sorted[..n], &[1, 2, 3]);
}
