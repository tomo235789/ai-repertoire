---
id: date-format-iso
lang: csharp
title: 日付を ISO 8601 形式の文字列にする
tags: [日付フォーマット, ISO 8601, 文字列化, タイムゾーン, format, iso, date-string, timestamp]
lib: stdlib
fn: DateTimeOffset.ToString
since: "6.0"
verified: 2026-09-17
status: public
---

`DateTimeOffset` を `"o"`（ラウンドトリップ）書式で ISO 8601 文字列（`2024-02-29T13:45:07.0000000+09:00`）にする。API の送信値やログの日時表記に使う。

## Signature

```csharp
public string ToString(string? format)
```

## Usage

```csharp
using System;

var d = new DateTimeOffset(2024, 2, 29, 13, 45, 7, TimeSpan.FromHours(9));
d.ToString("o");                                    // => "2024-02-29T13:45:07.0000000+09:00"
d.UtcDateTime.ToString("o");                        // => "2024-02-29T04:45:07.0000000Z"
new DateTime(2024, 2, 29, 13, 45, 7).ToString("o"); // => "2024-02-29T13:45:07.0000000"（Kind Unspecified）
DateTimeOffset.Parse(d.ToString("o")) == d;         // => true（逆変換）
```

## Contract

- `DateTimeOffset` の `"o"` は常に小数 7 桁と `+09:00` 形式のオフセットを出す。オフセット 0 でも `+00:00` であり `Z` にはならない
- `DateTime` の `"o"` は `Kind` で末尾が変わる。`Unspecified` はオフセット無し、`Utc` は `Z`、`Local` は実行環境のオフセット（`new DateTimeOffset(dt).ToString("o")` と同じ）
- カルチャに依存しない。`CurrentCulture` が `ja-JP` / `ar-SA` / `th-TH` でも同じ文字列（既定の `ToString()` はカルチャ依存）
- 年は 4 桁ゼロ埋め（`0001-01-01T00:00:00.0000000+00:00`）
- `DateTimeOffset.Parse` / `ParseExact(s, "o", ...)` で元の値とオフセットに正確に戻る
- `DateTime.Parse` は `Z` やオフセット付きの文字列を **ローカル時刻に変換して `Kind = Local`** で返す。`DateTimeStyles.RoundtripKind` を渡すと `Z` は `Kind = Utc` のまま、オフセット無しは `Unspecified` のまま戻る
- 入力を変更しない純粋関数（`DateTimeOffset` / `DateTime` は struct）

## Alternatives

- 小数無し・オフセット付きなら書式 `"yyyy-MM-dd'T'HH:mm:ssK"`（`K` は `DateTimeOffset` ではオフセット、`DateTime` では `Kind` に応じて `Z` / オフセット / 空）
- 常に `Z` 付きの UTC にしたいなら `d.UtcDateTime.ToString("o")`
- 日付だけなら `DateOnly.ToString("o")`（`2024-02-29`）。`"s"` はオフセット無しの `2024-02-29T13:45:07`、`"u"` は UTC に変換した `2024-02-29 04:45:07Z`
- 現在時刻は `DateTime.Now`（`Kind = Local`）ではなく `DateTimeOffset.UtcNow` / `DateTimeOffset.Now` を使うとオフセットが失われない

## Pitfalls

- TypeScript（date-fns の `formatISO`）はオフセット 0 で `Z` を出しミリ秒を出さないが、`"o"` は `+00:00` と小数 7 桁。`Z` が要る API には `UtcDateTime` を通す。Python の `isoformat()` も `+00:00` で、小数はマイクロ秒 6 桁
- `DateTime.Parse` はローカル時刻に変換してしまうので、`"o"` で書き出した UTC を読み戻すと時刻が変わる。`DateTimeStyles.RoundtripKind` を付けるか `DateTimeOffset.Parse` を使う
- コンストラクタで作った `DateTime` は `Kind = Unspecified` でオフセットが付かない。受け手はどのタイムゾーンか判断できないので、外部に出す値は `DateTimeOffset` で持つ
- `"o"` 以外の書式（`"g"` や既定の `ToString()`）はカルチャで区切りや順序が変わる。ログにも `"o"` を使う

## Test

`examples/DateFormatIsoTests.cs`
