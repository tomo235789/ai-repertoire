---
id: date-format-iso
lang: ruby
title: 日付を ISO 8601 形式の文字列にする
tags: [日付フォーマット, ISO 8601, 文字列化, タイムゾーン, format, iso, date-string, timestamp, xmlschema]
lib: stdlib
fn: Time#iso8601
since: "1.9"
verified: 2026-09-17
status: public
---

Time を ISO 8601 文字列（`2024-02-29T13:45:07+09:00`）にする。API の送信値やログの日時表記に使う。`require "time"` で逆変換の `Time.iso8601` も使える。

## Signature

```ruby
time.iso8601(fraction_digits = 0) -> string
```

## Usage

```ruby
require "time"

t = Time.new(2024, 2, 29, 13, 45, 7.123456r, "+09:00")
t.iso8601                   # => "2024-02-29T13:45:07+09:00"
t.iso8601(3)                # => "2024-02-29T13:45:07.123+09:00"
t.getutc.iso8601            # => "2024-02-29T04:45:07Z"
Time.iso8601("2024-02-29T13:45:07+09:00")  # => 2024-02-29 13:45:07 +0900
```

## Contract

- レシーバのオフセットで整形する。`utc?` が真なら末尾は `Z`、それ以外は `+09:00` / `-03:00` の形。オフセットが 0 でも `Time.new(..., "+00:00")` のように `utc?` が偽なら `+00:00` になる
- `fraction_digits`（既定 `0`）で小数秒の桁数を固定する。`0` なら小数秒を出さない。正の桁数を指定すると小数秒が 0 でも `.000` のように桁数どおり出し、桁を落とすときは切り捨て（`7.9999` 秒を 3 桁にすると `.999`）。9 桁を超える指定も受け付け、ナノ秒より下は `0` で埋める
- 年は 4 桁ゼロ埋め（`0001-01-01T00:00:00Z`）。5 桁以上や負の年はそのまま出す
- `fraction_digits` が整数に変換できない（`String`、`nil`）と `TypeError`（3.4 以降。core の C 実装に移ったため。3.3 以前の time gem 実装は `to_i` で受け入れ、`"3"` は 3 桁、`nil` は 0 桁として動く）
- 入力を変更しない。返り値は新しい `String`
- `xmlschema` は同じメソッド（別名）
- `Date#iso8601` は `"2024-02-29"` の日付のみ。`DateTime#iso8601(n)` は `Time` と同じ形式
- `Time.iso8601(str)` は逆変換。オフセット付きならそのオフセットを保った `Time`、`Z` なら `utc?` が真の `Time`、オフセット無しならローカル時刻として解釈する。日付のみ（`"2024-02-29"`）、区切りが空白、basic 形式（`20240229T134507Z`）は `ArgumentError`（`invalid xmlschema format`）

## Alternatives

- UTC に揃えたいなら `t.getutc.iso8601`（`t.utc.iso8601` はレシーバを UTC に **書き換える**。後述）
- 任意の書式は `t.strftime("%FT%T%:z")`（`%:z` は `+09:00`、`%z` は `+0900`）
- 現在時刻は `Time.now.iso8601`。特定のオフセットで作るなら `Time.now.getlocal("+09:00")`
- 日付だけなら `t.to_date.iso8601` か `t.strftime("%F")`

## Pitfalls

- `Time#utc` / `Time#localtime` は破壊的で、レシーバ自身のオフセットを変える。`t.utc.iso8601` と書くとその後の `t.iso8601` も `Z` になる。非破壊の `getutc` / `getlocal` を使う
- TypeScript（date-fns）の `formatISO` はオフセット 0 なら常に `Z` を出すが、Ruby は `utc?` で決まる。`+00:00` のオフセットで作った `Time` は `Z` にならない。Python の `isoformat()` は UTC でも `+00:00` で `Z` を出さない
- Python の `isoformat()` はマイクロ秒があれば自動で `.123456` を付けるが、Ruby は `fraction_digits` を指定しない限り小数秒を出さない（切り捨て）。ミリ秒が必要なら `iso8601(3)` を明示する
- `Time#to_s` は `"2024-02-29 13:45:07 +0900"` で ISO 8601 ではない。`to_json`（`json` gem）も `to_s` の形式で出すので、API に渡す JSON には `iso8601` した文字列を入れる

## Test

`examples/date-format-iso_test.rb`
