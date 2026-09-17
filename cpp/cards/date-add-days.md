---
id: date-add-days
lang: cpp
title: 日付に日数を加算する
tags: [日付加算, 日数, 期限計算, カレンダー, add-days, date-arithmetic, chrono, sys-days]
lib: stdlib
fn: std::chrono::sys_days
since: "C++20"
verified: 2026-09-17
status: public
---

`sys_days`（日単位の時刻点）に `days{n}` を足して新しい日付を得る（負数で減算）。期限日や有効期間の計算に使う。`year_month_day` は直接足せないので `sys_days` を経由する。

## Signature

```cpp
namespace std::chrono { using sys_days = time_point<system_clock, days>; }  // 標準が std::chrono 内で宣言する別名。sys_days + days{n} → sys_days
```

## Usage

```cpp
#include <chrono>
using namespace std::chrono;

sys_days d = 2024y/2/29;            // year_month_day から暗黙変換
year_month_day r = d + days{1};     // => 2024-03-01（sys_days から暗黙変換）
d - days{1};                        // => 2024-02-28
d + days{366};                      // => 2025-03-01
sys_seconds t = d + 13h + 45min + 7s;
t + days{1};                        // => 2024-03-01 13:45:07（時刻は保たれる）
```

## Contract

- 新しい値を返し、元の `sys_days` は変わらない（値型）
- 月末・年末・うるう年の繰り越しは暦どおり（`2024-02-29` + 1 → `2024-03-01`、+ 365 → `2025-02-28`、`2024-12-31` + 1 → `2025-01-01`）。負数で過去へ戻る
- `days{1}` は正確に 24 時間（`days{1} == 24h`）。`sys_days` は UTC 基準で夏時間が無いので、常に 1 暦日 = 24 時間。`sys_seconds` などに足しても時・分・秒はそのまま保たれる
- `year_month_day` と `sys_days` は互いに暗黙変換できる。`ok()` が偽の `year_month_day`（`2023-02-29`）を `sys_days` にすると繰り越して正規化される（`2023-03-01`）
- `year_month_day + days{1}` はコンパイルエラー。`year_month_day` に足せるのは `months` と `years` だけで、`2024-01-31 + months{1}` は日を正規化せず `2024-02-31`（`ok()` が偽）になる。`sys_days` に変換すると `2024-03-02` に繰り越す
- `days{1.5}` はコンパイルエラー（整数型の日数だけ）。時間単位で足すなら `36h`
- 例外を投げない。`constexpr` で定数式に使える

## Alternatives

- 週は `weeks{1}`（= `days{7}`）。月・年は `year_month_day` に `months{1}` / `years{1}` を足し、月末に丸めたいなら `ymd.year()/ymd.month()/last` で最終日を取る（`2024-01-31` + 1 か月 → `2024-02-29`）
- 壁時計の時刻を保ったまま日付を進めたい（夏時間をまたぐ）なら `zoned_time` の `get_local_time() + days{1}` を同じゾーンで `zoned_time` に戻す。`get_sys_time() + days{1}` は経過時間 24 時間で壁時計が 1 時間ずれる
- 2 つの日付の差は `(d2 - d1).count()`（date-diff-days）

## Pitfalls

- TypeScript（date-fns の `addDays`）はローカルの壁時計の日付を進めるので夏時間をまたぐと経過時間が 23 / 25 時間になるが、`sys_days + days{1}` は常に 24 時間。ローカルの日付操作は `local_days` や `zoned_time` で行う
- Python の `timedelta(days=1.5)` は 36 時間だが、C++ の `days` は整数のみでコンパイルエラーになる。小数を渡す事故は起きない
- `year_month_day` に `months{1}` を足すと月末が壊れる（`2024-02-31`）。`ok()` を確認するか `last` で丸める
- `sys_days` は日付だけを持つ。時刻付きの `sys_seconds` を `sys_days` に戻すには `floor<days>(t)` を使う（`year_month_day{floor<days>(t)}`）

## Test

`examples/date-add-days_test.cpp`
