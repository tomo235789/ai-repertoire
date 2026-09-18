---
id: number-sum-by
lang: rust
title: 配列の各要素から取り出した数値を合計する
tags: [合計, 集計, 合算, オーバーフロー, sum, sum-by, total, aggregate]
lib: stdlib
fn: Iterator::sum
since: "1.11"
verified: 2026-09-17
status: public
---

各要素から数値を取り出して合計する。オブジェクト配列の数量や金額の集計に使う。`map` で取り出して `sum` で畳み込み、返り値の型は注釈で指定する。

## Signature

```rust
fn sum<S>(self) -> S where Self: Sized, S: Sum<Self::Item>
```

## Usage

```rust
struct Item { qty: i64 }

let items = vec![Item { qty: 2 }, Item { qty: 3 }];
let total: i64 = items.iter().map(|item| item.qty).sum();
// => 5
items.iter().map(|item| item.qty).sum::<i64>(); // 型注釈の別の書き方
```

## Contract

- 入力を変更しない。`iter()` は要素を借用するので合計後も `items` はそのまま使える
- 返り値の型は推論されないので `let total: i64 = ...` か `sum::<i64>()` で指定する。`Sum<i64>` と `Sum<&i64>` の両方が実装されているので、`&i64` の列は `map` 無しでも合計できる
- 取り出し関数は各要素につきちょうど 1 回、先頭から順に呼ばれる
- 空なら整数は `0`、`f64` は `-0.0`（`== 0.0` は真）
- **整数のオーバーフローは `overflow-checks` が有効なら panic**（`attempt to add with overflow`）、**無効なら 2 の補数でラップ** する（`i32::MAX + 1` は `-2147483648`）。既定はデバッグビルドで有効、リリースビルドで無効だが、プロファイル設定（`[profile.release] overflow-checks = true` など）で変えられる
- `f64` の合計は左からの素朴な加算で補正は無い。`[0.1; 10]` の合計は `0.9999999999999999`。要素に `NaN` があれば `NaN`、`inf` と `-inf` を両方含むと `NaN`
- `Option<T>` / `Result<T, E>` の列を `sum` すると `None` / `Err` が 1 つでもあれば全体がそれになる（`[Some(1), None]` → `None`）

## Alternatives

- オーバーフローを検出するなら `try_fold(0_i64, |acc, x| acc.checked_add(x))`（溢れたら `None`）。明示的にラップさせるなら `fold(0, |acc, x| acc.wrapping_add(x))`
- 型を広げてから合計する（`map(|x| x as i64)`）と小さい型の溢れを避けられる
- 積は `product()`。平均は number-mean
- `f64` の誤差を抑えたいなら Kahan / Neumaier 加算を自前で書く（標準には無い）

## Pitfalls

- TypeScript（es-toolkit の `sumBy`）と Python の `sum` は溢れないが、Rust は固定幅整数。件数 × 最大値が型に収まるか確認する。金額などは `i64` か `i128` で持つ
- Python 3.12 の `sum` は `float` を補正付きで足すので `sum([0.1] * 10)` が `1.0` になるが、Rust は `0.9999999999999999`
- 型注釈を忘れると `type annotations needed` のコンパイルエラー。返り値の型は要素の型と違ってもよい（`u8` を `map(|x| x as u32)` してから `sum::<u32>()`）
- 金額など誤差を許せない値は整数（最小単位）で合計する

## Test

`tests/number_sum_by.rs`
