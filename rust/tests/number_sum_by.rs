//! number-sum-by: Iterator::sum の契約を検証する

struct Item {
    name: &'static str,
    qty: i64,
}

fn items() -> Vec<Item> {
    vec![Item { name: "a", qty: 2 }, Item { name: "b", qty: 3 }]
}

#[test]
fn sums_extracted_values_without_consuming_input() {
    // map で取り出した値を合計する。iter() は借用なので入力はそのまま使える
    let items = items();
    let total: i64 = items.iter().map(|item| item.qty).sum();
    assert_eq!(total, 5);
    assert_eq!(items.iter().map(|item| item.qty).sum::<i64>(), 5);
    assert_eq!(items[0].name, "a");
}

#[test]
fn sum_of_references_without_map() {
    // Sum<&i64> があるので参照の列も直接合計できる。型は要素と違ってもよい
    let v = [1_i64, 2, 3];
    let total: i64 = v.iter().sum();
    assert_eq!(total, 6);
    let widened: u32 = [200_u8, 100].iter().map(|&x| x as u32).sum();
    assert_eq!(widened, 300);
}

#[test]
fn extractor_called_once_per_element_in_order() {
    // 取り出し関数は各要素につき 1 回、先頭から順に呼ばれる
    let mut seen = Vec::new();
    let total: i32 = [10, 20, 30]
        .iter()
        .map(|&x| {
            seen.push(x);
            x
        })
        .sum();
    assert_eq!(total, 60);
    assert_eq!(seen, vec![10, 20, 30]);
}

#[test]
fn empty_is_zero_for_int_and_negative_zero_for_f64() {
    // 空の合計は整数なら 0、f64 なら -0.0
    let ints: i64 = Vec::<Item>::new().iter().map(|item| item.qty).sum();
    assert_eq!(ints, 0);
    let floats: f64 = Vec::<f64>::new().iter().sum();
    assert_eq!(floats, 0.0);
    assert!(floats.is_sign_negative());
}

#[test]
fn integer_overflow_follows_overflow_checks() {
    // overflow-checks が有効なら panic、無効なら 2 の補数でラップ。
    // プロファイルに依らず通るよう、通常の加算がどちらの挙動かを先に調べて突き合わせる
    let checks_enabled =
        std::panic::catch_unwind(|| std::hint::black_box(i32::MAX) + std::hint::black_box(1)).is_err();
    match std::panic::catch_unwind(|| [i32::MAX, 1].iter().sum::<i32>()) {
        Err(payload) => {
            assert!(checks_enabled);
            let msg = payload
                .downcast_ref::<&str>()
                .copied()
                .or_else(|| payload.downcast_ref::<String>().map(String::as_str))
                .unwrap_or("");
            assert_eq!(msg, "attempt to add with overflow");
        }
        Ok(total) => {
            assert!(!checks_enabled);
            assert_eq!(total, i32::MIN);
        }
    }
}

#[test]
fn checked_and_wrapping_alternatives() {
    // checked_add で検出、wrapping_add で明示的にラップ、型を広げて回避
    let checked = [i32::MAX, 1].iter().try_fold(0_i32, |acc, &x| acc.checked_add(x));
    assert_eq!(checked, None);
    let wrapped = [i32::MAX, 1].iter().fold(0_i32, |acc, &x| acc.wrapping_add(x));
    assert_eq!(wrapped, i32::MIN);
    let widened: i64 = [i32::MAX, 1].iter().map(|&x| x as i64).sum();
    assert_eq!(widened, 2_147_483_648);
}

#[test]
fn f64_has_no_correction_and_propagates_nan() {
    // f64 は素朴な加算。NaN は伝播し、inf + -inf は NaN
    let tenth: f64 = [0.1; 10].iter().sum();
    assert_eq!(tenth, 0.9999999999999999);
    let pair: f64 = [0.1, 0.2].iter().sum();
    assert_eq!(pair, 0.30000000000000004);
    let with_nan: f64 = [1.0, f64::NAN].iter().sum();
    assert!(with_nan.is_nan());
    let infs: f64 = [f64::INFINITY, f64::NEG_INFINITY].iter().sum();
    assert!(infs.is_nan());
}

#[test]
fn option_and_result_short_circuit() {
    // Option / Result の列は None / Err が 1 つでもあれば全体がそれになる
    let some: Option<i32> = [Some(1), Some(2)].into_iter().sum();
    assert_eq!(some, Some(3));
    let none: Option<i32> = [Some(1), None].into_iter().sum();
    assert_eq!(none, None);
    let err: Result<i32, &str> = [Ok(1), Err("bad"), Ok(2)].into_iter().sum();
    assert_eq!(err, Err("bad"));
}

#[test]
fn product_alternative() {
    // 積は product()
    let p: i64 = items().iter().map(|item| item.qty).product();
    assert_eq!(p, 6);
}
