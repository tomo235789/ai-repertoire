//! カード collection-group-by（Itertools::into_group_map_by）の Contract を検証するテスト

use itertools::Itertools;
use std::collections::{BTreeMap, HashMap};

/// 各グループは出現順で、キーは HashMap に集まる
#[test]
fn groups_preserve_element_order() {
    let items = vec![("a", 1), ("b", 2), ("a", 3)];
    let groups: HashMap<&str, Vec<(&str, i32)>> = items.into_iter().into_group_map_by(|x| x.0);
    assert_eq!(groups.len(), 2);
    assert_eq!(groups["a"], vec![("a", 1), ("a", 3)]);
    assert_eq!(groups["b"], vec![("b", 2)]);
    let mut keys: Vec<&str> = groups.keys().copied().collect();
    keys.sort();
    assert_eq!(keys, vec!["a", "b"]);
}

/// iter() なら参照、into_iter() なら所有権が移る
#[test]
fn borrows_or_takes_ownership() {
    let names = vec!["apple".to_string(), "banana".to_string(), "avocado".to_string()];
    let by_ref: HashMap<char, Vec<&String>> = names.iter().into_group_map_by(|s| s.chars().next().unwrap());
    assert!(std::ptr::eq(by_ref[&'a'][0], &names[0]));
    assert_eq!(names.len(), 3);
    let owned: HashMap<usize, Vec<String>> = names.into_iter().into_group_map_by(|s| s.len());
    assert_eq!(owned[&5], vec!["apple"]);
}

/// 即時評価で、キー関数は各要素につき 1 回ずつ先頭から順に呼ばれる
#[test]
fn eager_and_calls_key_once_in_order() {
    let mut seen = vec![];
    let groups: HashMap<bool, Vec<i32>> = [3, 1, 2].into_iter().into_group_map_by(|n| {
        seen.push(*n);
        *n > 1
    });
    assert_eq!(seen, vec![3, 1, 2]);
    assert_eq!(groups[&true], vec![3, 2]);
    assert_eq!(groups[&false], vec![1]);
}

/// キーは == とハッシュで比較される
#[test]
fn compares_keys_by_value() {
    let rows = vec![("x".to_string(), 1), ("x".to_string(), 2)];
    let groups: HashMap<String, Vec<i32>> = rows.into_iter().map(|(k, v)| (k, v)).into_group_map();
    assert_eq!(groups["x"], vec![1, 2]);
}

/// 空の入力は空の HashMap
#[test]
fn empty_input_gives_empty_map() {
    let groups: HashMap<i32, Vec<i32>> = std::iter::empty::<i32>().into_group_map_by(|x| *x);
    assert!(groups.is_empty());
}

/// キー順が要るなら BTreeMap に fold で集める
#[test]
fn btree_map_for_sorted_keys() {
    let items = vec![("b", 2), ("a", 1), ("b", 3)];
    let groups = items.into_iter().fold(BTreeMap::new(), |mut m, x| {
        m.entry(x.0).or_insert_with(Vec::new).push(x);
        m
    });
    let keys: Vec<&str> = groups.keys().copied().collect();
    assert_eq!(keys, vec!["a", "b"]);
    assert_eq!(groups["b"], vec![("b", 2), ("b", 3)]);
}

/// chunk_by は隣接する同キーしかまとめない（into_group_map_by との違い）
#[test]
fn chunk_by_only_groups_adjacent() {
    let items = [("a", 1), ("b", 2), ("a", 3)];
    let chunks: Vec<(&str, Vec<i32>)> = items
        .iter()
        .chunk_by(|x| x.0)
        .into_iter()
        .map(|(k, g)| (k, g.map(|x| x.1).collect()))
        .collect();
    assert_eq!(chunks, vec![("a", vec![1]), ("b", vec![2]), ("a", vec![3])]);
}
