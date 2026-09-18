---
id: date-format-iso
lang: rust
title: 日付を ISO 8601 形式の文字列にする
tags: [日付フォーマット, ISO 8601, 文字列化, タイムゾーン, format, iso, rfc3339, timestamp]
lib: chrono
fn: DateTime::to_rfc3339
since: "0.4"
verified: 2026-09-17
status: public
---

`DateTime<Tz>` を ISO 8601 / RFC 3339 文字列（`2024-02-29T13:45:07+09:00`）にする。API の送信値やログの日時表記に使う。`to_rfc3339_opts` で秒未満の桁と `Z` 表記を固定できる。

## Signature

```rust
pub fn to_rfc3339(&self) -> String
```

## Usage

```rust
use chrono::{DateTime, FixedOffset, SecondsFormat, TimeZone, Utc};

let utc = Utc.with_ymd_and_hms(2024, 2, 29, 13, 45, 7).unwrap();
utc.to_rfc3339();                               // => "2024-02-29T13:45:07+00:00"
utc.to_rfc3339_opts(SecondsFormat::Secs, true); // => "2024-02-29T13:45:07Z"
let jst = FixedOffset::east_opt(9 * 3600).unwrap().with_ymd_and_hms(2024, 2, 29, 13, 45, 7).unwrap();
jst.to_rfc3339();                               // => "2024-02-29T13:45:07+09:00"
DateTime::parse_from_rfc3339("2024-02-29T13:45:07+09:00").unwrap() == jst; // => true
```

## Contract

- `DateTime<Tz>` が持つオフセットを `+09:00` の形で付ける。UTC は `+00:00` であり `Z` にはならない。実行環境のタイムゾーンには依存しない（`Local::now()` にはローカルのオフセットが付く）
- `to_rfc3339()` は秒未満が 0 なら秒まで、0 でなければ末尾の 0 を省いてナノ秒 9 桁まで出す（`.123` / `.123456789`）
- `to_rfc3339_opts(secform, use_z)` で桁を固定する。`SecondsFormat::Secs` は常に秒まで、`Millis` は常に `.000`、`Nanos` は常に 9 桁、`AutoSi` は 0 / 3 / 6 / 9 桁のうち必要な最小。`use_z = true` はオフセット 0 のときだけ `Z` にする（`+09:00` はそのまま）
- 桁を落とすときは切り捨て（`999_999` µs を `Millis` で `.999`）
- 年は 4 桁ゼロ埋め（`0001-01-01T00:00:00+00:00`）。5 桁以上と負の年には `+12345-` / `-0001-` のように符号が付く
- `NaiveDateTime` にはタイムゾーンが無いので `to_rfc3339` は無い。`Display` は `2024-02-29 13:45:07`（空白区切り）、`Debug` は `2024-02-29T13:45:07`。`format("%+")` は `Display` がエラーを返し `to_string()` が panic する
- 逆変換は `DateTime::parse_from_rfc3339(s)`（`DateTime<FixedOffset>` を返す）。`Z` は `+00:00` として読み、オフセットの無い文字列は `Err`。`to_rfc3339` の出力を戻すと元と等しい
- 入力を変更しない（`&self`）。新しい `String` を返す

## Alternatives

- `format("%+")` は `to_rfc3339` と同じ出力。任意の書式は `format("%Y-%m-%dT%H:%M:%S%:z")`（`%z` はコロン無しの `+0900`）
- `Debug`（`{:?}`）も `2024-02-29T13:45:07+09:00` の形だが、`Display`（`{}`）は空白区切りの `2024-02-29 13:45:07 +09:00` で ISO 8601 ではない
- UTC に変換してから整形するなら `dt.with_timezone(&Utc).to_rfc3339_opts(SecondsFormat::Secs, true)`（JST の `13:45` は `04:45Z`）
- 日付だけなら `dt.date_naive().to_string()`（`2024-02-29`）か `format("%Y-%m-%d")`
- 文字列から `DateTime<Utc>` に直接欲しいなら `s.parse::<DateTime<Utc>>()`（オフセットは UTC に換算される）

## Pitfalls

- TypeScript（date-fns の `formatISO`）はオフセット 0 を `Z` にし秒未満を出さない。同じにするなら `to_rfc3339_opts(SecondsFormat::Secs, true)`。Python の `isoformat()` は `+00:00` でマイクロ秒 6 桁なので既定の `to_rfc3339()` に近い（Rust は最大 9 桁）
- `NaiveDateTime` を `to_string()` すると空白区切りになる。`T` 区切りが欲しければ `and_utc()` でタイムゾーンを付けるか `format("%Y-%m-%dT%H:%M:%S")` を使う
- `Local::now()` のオフセットは実行環境の `TZ` に依存する。サーバー間で揃えたいなら `Utc::now()` を使う
- うるう秒（ナノ秒が 10^9 以上の値）は `23:59:60` と出力される。受け手がパースできるか確認する

## Test

`tests/date_format_iso.rs`
