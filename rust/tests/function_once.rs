//! function-once: std::sync::OnceLock::get_or_init の契約を検証する

use std::cell::OnceCell;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{LazyLock, OnceLock};
use std::thread;
use std::time::Duration;

#[test]
fn runs_initializer_once_and_returns_same_reference() {
    // 1 回目だけ実行し、2 回目以降は同じ値への参照。別のクロージャは無視される
    static CONFIG: OnceLock<String> = OnceLock::new();
    static CALLS: AtomicUsize = AtomicUsize::new(0);
    let first = CONFIG.get_or_init(|| {
        CALLS.fetch_add(1, Ordering::SeqCst);
        "mode=test".to_string()
    });
    let second = CONFIG.get_or_init(|| {
        CALLS.fetch_add(1, Ordering::SeqCst);
        "other".to_string()
    });
    assert_eq!(first, "mode=test");
    assert!(std::ptr::eq(first, second));
    assert_eq!(CALLS.load(Ordering::SeqCst), 1);
}

#[test]
fn concurrent_calls_initialize_exactly_once() {
    // 複数スレッドから同時に呼んでも 1 回だけ実行され、全員が同じ値を受け取る
    static VALUE: OnceLock<u64> = OnceLock::new();
    static CALLS: AtomicUsize = AtomicUsize::new(0);
    let handles: Vec<_> = (0..8)
        .map(|i| {
            thread::spawn(move || {
                *VALUE.get_or_init(|| {
                    CALLS.fetch_add(1, Ordering::SeqCst);
                    thread::sleep(Duration::from_millis(10));
                    i
                })
            })
        })
        .collect();
    let values: Vec<u64> = handles.into_iter().map(|h| h.join().unwrap()).collect();
    assert_eq!(CALLS.load(Ordering::SeqCst), 1);
    assert!(values.iter().all(|&v| v == values[0]));
}

#[test]
fn panicking_initializer_is_retried() {
    // 初期化中に panic すると未初期化のままで、次の呼び出しで再実行される
    static VALUE: OnceLock<i32> = OnceLock::new();
    static CALLS: AtomicUsize = AtomicUsize::new(0);
    let result = std::panic::catch_unwind(|| {
        VALUE.get_or_init(|| {
            CALLS.fetch_add(1, Ordering::SeqCst);
            panic!("boom")
        })
    });
    assert!(result.is_err());
    assert_eq!(VALUE.get(), None);
    let v = VALUE.get_or_init(|| {
        CALLS.fetch_add(1, Ordering::SeqCst);
        42
    });
    assert_eq!(*v, 42);
    assert_eq!(CALLS.load(Ordering::SeqCst), 2);
}

#[test]
fn get_and_set() {
    // get は未初期化なら None。set は 1 回目だけ Ok で、2 回目は値を Err で返す
    let cell: OnceLock<i32> = OnceLock::new();
    assert_eq!(cell.get(), None);
    assert_eq!(cell.set(1), Ok(()));
    assert_eq!(cell.set(2), Err(2));
    assert_eq!(cell.get(), Some(&1));
}

#[test]
fn take_and_get_mut_require_exclusive_access() {
    // &mut で所有していれば take で未初期化に戻せ、get_mut で書き換えられる
    let mut cell: OnceLock<i32> = OnceLock::new();
    cell.get_or_init(|| 7);
    if let Some(v) = cell.get_mut() {
        *v = 9;
    }
    assert_eq!(cell.get(), Some(&9));
    assert_eq!(cell.take(), Some(9));
    assert_eq!(cell.get(), None);
    assert_eq!(*cell.get_or_init(|| 1), 1);
}

#[test]
fn lazy_lock_and_once_cell_alternatives() {
    // LazyLock は宣言時にクロージャを固定し、OnceCell は単一スレッド用
    static LAZY_CALLS: AtomicUsize = AtomicUsize::new(0);
    static LAZY: LazyLock<Vec<i32>> = LazyLock::new(|| {
        LAZY_CALLS.fetch_add(1, Ordering::SeqCst);
        vec![1, 2]
    });
    assert_eq!(*LAZY, vec![1, 2]);
    assert_eq!(LAZY.len(), 2);
    assert_eq!(LAZY_CALLS.load(Ordering::SeqCst), 1);

    let cell: OnceCell<i32> = OnceCell::new();
    assert_eq!(*cell.get_or_init(|| 3), 3);
    assert_eq!(*cell.get_or_init(|| 4), 3);
}
