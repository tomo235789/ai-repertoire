//! string-pad: format! の幅指定の契約を検証する

use std::fmt;

#[test]
fn aligns_left_right_center() {
    // 寄せ方の 3 種類。文字列の既定は左寄せ、数値の既定は右寄せ
    assert_eq!(format!("{:<8}", "abc"), "abc     ");
    assert_eq!(format!("{:>8}", "abc"), "     abc");
    assert_eq!(format!("{:^8}", "abc"), "  abc   ");
    assert_eq!(format!("{:8}", "abc"), "abc     ");
    assert_eq!(format!("{:8}", 42), "      42");
}

#[test]
fn center_puts_extra_on_right() {
    // 中央寄せで余りが奇数なら右側が 1 文字多い
    assert_eq!(format!("{:^4}", "abc"), "abc ");
    assert_eq!(format!("{:^5}", "ab"), " ab  ");
    assert_eq!(format!("{:^7}", "ab"), "  ab   ");
    assert_eq!(format!("{:^6}", "ab"), "  ab  ");
}

#[test]
fn fill_char_is_single_char() {
    // 埋め文字は寄せ記号の直前に 1 文字。任意の char を使える
    assert_eq!(format!("{:*<8}", "abc"), "abc*****");
    assert_eq!(format!("{:*^8}", "abc"), "**abc***");
    assert_eq!(format!("{:0>5}", "42"), "00042");
    assert_eq!(format!("{:日<5}", "ab"), "ab日日日");
}

#[test]
fn width_from_arguments() {
    // 幅は変数（usize）・位置引数・名前付き引数で指定できる
    let width: usize = 6;
    assert_eq!(format!("{:>width$}", "abc"), "   abc");
    assert_eq!(format!("{:>1$}", "abc", 7), "    abc");
    assert_eq!(format!("{:^w$}", "ab", w = 6), "  ab  ");
}

#[test]
fn width_counts_chars_not_bytes() {
    // 幅は char の個数。全角は 1、結合文字は 2、ZWJ 絵文字は各コードポイント
    assert_eq!(format!("{:>5}", "日本語"), "  日本語");
    assert_eq!(format!("{:>4}", "e\u{301}"), "  e\u{301}");
    assert_eq!(format!("{:>2}", "😀"), " 😀");
    assert_eq!(format!("{:>6}", "👨\u{200d}👩\u{200d}👧"), " 👨\u{200d}👩\u{200d}👧");
}

#[test]
fn width_smaller_than_string_is_noop() {
    // 幅が文字数以下ならそのまま。切り詰めない
    assert_eq!(format!("{:>3}", "abc"), "abc");
    assert_eq!(format!("{:>2}", "abc"), "abc");
    assert_eq!(format!("{:^0}", "abc"), "abc");
    assert_eq!(format!("{:>4}", ""), "    ");
}

#[test]
fn returns_new_string_without_mutating_input() {
    // 新しい String を返し、元の値はそのまま
    let s = String::from("abc");
    let padded = format!("{:>5}", s);
    assert_eq!(padded, "  abc");
    assert_eq!(s, "abc");
}

#[test]
fn zero_padding_numbers_and_truncation() {
    // 数値の {:05} は符号を保つ。精度指定は文字列を切り詰める
    assert_eq!(format!("{:05}", 42), "00042");
    assert_eq!(format!("{:05}", -42), "-0042");
    assert_eq!(format!("{:.2}", "abcdef"), "ab");
    assert_eq!(format!("{:>8.3}", "abcdef"), "     abc");
}

struct IgnoresPadding;

impl fmt::Display for IgnoresPadding {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "dd")
    }
}

struct RespectsPadding;

impl fmt::Display for RespectsPadding {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        f.pad("dd")
    }
}

#[test]
fn custom_display_needs_pad_to_honor_width() {
    // write! で書いた Display は幅を無視し、f.pad なら幅が効く
    assert_eq!(format!("{:>6}", IgnoresPadding), "dd");
    assert_eq!(format!("{:>6}", RespectsPadding), "    dd");
    assert_eq!(format!("{:^6}", RespectsPadding), "  dd  ");
}
