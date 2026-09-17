---
id: date-format-iso
lang: cpp
title: 日付を ISO 8601 形式の文字列にする
tags: [日付フォーマット, ISO 8601, 文字列化, タイムゾーン, format, iso, date-string, timestamp]
lib: stdlib
fn: std::format
since: "C++20"
verified: 2026-09-17
status: public
---

`<chrono>` の時刻点を ISO 8601 文字列（`2024-02-29T13:45:07Z`）にする。API の送信値やログの日時表記に使う。`sys_time` は UTC なので末尾の `Z` はリテラルで書く。

## Signature

```cpp
template<class... Args> std::string std::format(std::format_string<Args...> fmt, Args&&... args);  // chrono の書式は "{:%FT%TZ}" "{:%F}" "{:%Ez}" "{:%Z}"
```

## Usage

```cpp
#include <chrono>
#include <format>
using namespace std::chrono;

sys_seconds t = sys_days{2024y/2/29} + 13h + 45min + 7s;          // UTC
std::format("{:%FT%TZ}", t);                                     // => "2024-02-29T13:45:07Z"
std::format("{:%FT%TZ}", floor<seconds>(system_clock::now()));   // 現在時刻を秒に切り捨てて
std::format("{:%FT%T%Ez}", zoned_time{"Asia/Tokyo", t});         // => "2024-02-29T22:45:07+09:00"
std::format("{:%F}", 2024y/2/29);                                // => "2024-02-29"
```

## Contract

- `%F` は `%Y-%m-%d`、`%T` は `%H:%M:%S`。年は 4 桁ゼロ埋め（`0001-01-01`）
- `sys_time`（`system_clock` の時刻点）は UTC として整形される。`%Z` は `"UTC"`、`%z` は `"+0000"`、`%Ez` は `"+00:00"` になるので、`Z` が欲しければリテラルで書く
- 秒未満の桁は時刻点の精度で決まる。`sys_seconds` なら無し、ミリ秒精度なら `.123`（3 桁）、マイクロ秒なら 6 桁、`system_clock::now()` は libstdc++ ではナノ秒精度なので 9 桁。`floor<seconds>` / `floor<milliseconds>` で落とす。切り捨てであり四捨五入しない（`.999999999` → `.999`）
- `zoned_time{"Asia/Tokyo", t}` で地域時刻に変換すると `%Ez` が `+09:00`、`%Z` が `JST` になる。OS のタイムゾーンデータベースを使い、存在しないゾーン名は `std::runtime_error` を投げる
- `year_month_day` や `sys_days` にも `%F` が使える。`sys_days` に `%T` は `00:00:00`。タイムゾーンを持たない `local_time` に `%Z` / `%z` を使うと `std::format_error`（書式がリテラルならコンパイルエラー）
- `{}`（書式なし）は `2024-02-29 13:45:07` のように区切りが空白で、`T` も `Z` も付かない
- 入力を変更しない。書式文字列はコンパイル時に検査される

## Alternatives

- 区切り無しの basic 形式は `"{:%Y%m%dT%H%M%SZ}"`（`20240229T134507Z`）
- 実行環境のタイムゾーンで出すなら `zoned_time{current_zone(), t}` に `"{:%FT%T%Ez}"`
- 逆変換は `std::chrono::parse("%FT%TZ", tp)` を `istream >>` で使う（GCC 14 以降。GCC 13 には無い）
- 時刻部だけなら `"{:%T}"`、`hh_mm_ss` や `duration` も同じ書式で整形できる

## Pitfalls

- TypeScript（date-fns の `formatISO`）はローカルのオフセット付き・ミリ秒なし、Python の `isoformat()` は UTC でも `+00:00`。C++ は `sys_time` が常に UTC で、`Z` を付けるかどうかも秒未満の桁数も書式と型で自分で決める
- `system_clock::now()` をそのまま渡すと `13:45:07.123456789Z` のように 9 桁付く。API が秒精度を要求するなら `floor<seconds>` してから整形する
- `%Z` は `Z` ではなく `UTC` を出す。`Z` は書式のリテラル
- `zoned_time` はタイムゾーンデータベース（`/usr/share/zoneinfo`）が無い環境では使えない。UTC しか扱わないなら `sys_time` だけで済ませる

## Test

`examples/date-format-iso_test.cpp`
