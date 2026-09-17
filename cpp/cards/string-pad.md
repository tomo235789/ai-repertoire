---
id: string-pad
lang: cpp
title: 文字列を指定幅まで両側に埋める
tags: [パディング, 中央揃え, 固定幅, 文字埋め, pad, padding, center, fixed-width]
lib: stdlib
fn: std::format
since: "C++20"
verified: 2026-09-17
status: public
---

文字列の左右に文字を詰めて指定の幅にする。固定幅のテキスト表示やログの桁揃えで使う。`std::format` の配置指定（`<` `>` `^`）と幅で書く。

## Signature

```cpp
template<class... Args> std::string std::format(std::format_string<Args...> fmt, Args&&... args);  // 書式は "{:[埋め文字][<^>]幅}"
```

## Usage

```cpp
#include <format>

std::format("{:^8}", "abc");      // => "  abc   "（中央。余りは右が多い）
std::format("{:*^8}", "abc");     // => "**abc***"（埋め文字は配置の直前に 1 文字）
std::format("{:>8}", "abc");      // => "     abc"（右寄せ）
std::format("{:<8}", "abc");      // => "abc     "（左寄せ）
std::format("{:>{}}", "abc", 8);  // => "     abc"（幅を実行時に渡す）
std::format("{:^2}", "abc");      // => "abc"（幅以下ならそのまま）
```

## Contract

- `<` は左寄せ（右に埋める）、`>` は右寄せ、`^` は中央。省略時の配置は文字列が `<`、数値が `>`
- `^` の余りが奇数なら右側が 1 文字多い（`{:^5}` に `"ab"` → `" ab  "`）
- 埋め文字は省略時が半角スペース。配置指定の直前に 1 文字だけ書ける。実行時に `{}` で渡すことはできない（リテラル `"{:{}<6}"` はコンパイル時の書式検査で弾かれ、同じ文字列を `std::vformat` に渡すと実行時に `std::format_error`）
- 幅は `{}` で実行時に渡せる。負の値や整数以外を渡すと `std::format_error`、`0` はそのまま。書式リテラルに `0` 幅（`{:>0}`）は書けずコンパイルエラー
- 幅以下ならそのまま返す。切り詰めない。切り詰めるなら精度指定 `{:.2}`（`"abcdef"` → `"ab"`）。両方書くと `{:>6.2}` → `"    ab"`
- 空文字なら埋め文字だけで幅を埋める
- 幅の単位はライブラリの版で異なる。GCC 14 以降の libstdc++ は Unicode の推定表示幅（ASCII は 1、全角は 2 で `"あい"` は 4）、GCC 13 は UTF-8 のバイト数（`"あい"` は 6）。どちらもコードポイント数（`"あい"` は 2）ではない
- 書式文字列はコンパイル時に検査され、不正なら実行前に弾かれる。新しい `std::string` を返し、引数を変更しない

## Alternatives

- 数値のゼロ埋めは `std::format("{:06}", n)`（符号の後に `0` が入り `-42` は `"-00042"`）
- iostream なら `os << std::setw(8) << std::setfill('*') << std::right << s`（片側のみ。`<iomanip>`）
- 書式を実行時に組み立てるなら `std::vformat(fmt, std::make_format_args(args...))`（引数は左辺値で渡す）
- 片側だけ手で足すなら `std::string(n, ' ') + s` / `s.append(n, '*')`

## Pitfalls

- 長さの単位が言語で違う。TypeScript（es-toolkit の `pad`）は UTF-16 コード単位、Python の `str.center` はコードポイント、C++ は GCC 14 以降が表示幅、GCC 13 がバイト数。全角を含む列は GCC 14 以降なら表示幅で揃うが、GCC 13 では崩れる
- 結合文字や ZWJ 絵文字列の幅は版で変わる（GCC 14 以降はグラフェムクラスタ単位で `e` + U+0301 が幅 1、家族絵文字が幅 2）。厳密な桁揃えには依存しない
- Python の `str.center` は幅が奇数だと左に寄せることがあるが、`^` は常に右に寄せる（es-toolkit の `pad` や Python の f-string `^` と同じ）
- 埋め文字に全角（`{:あ^7}`）を書くと GCC 13 ではコンパイルエラー、GCC 16 では通る。ASCII に限る

## Test

`examples/string-pad_test.cpp`
