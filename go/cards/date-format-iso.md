---
id: date-format-iso
lang: go
title: 日付を ISO 8601 形式の文字列にする
tags: [日付フォーマット, ISO 8601, 文字列化, タイムゾーン, format, iso, rfc3339, timestamp]
lib: stdlib
fn: time.Time.Format
since: "1.0"
verified: 2026-09-17
status: public
---

`time.Time` を RFC 3339（ISO 8601 の実用プロファイル）の文字列 `2024-02-29T13:45:07+09:00` にする。API の送信値やログの日時表記に使う。

## Signature

```go
func (t Time) Format(layout string) string
```

## Usage

```go
import "time"

loc, _ := time.LoadLocation("Asia/Tokyo")
d := time.Date(2024, 2, 29, 13, 45, 7, 123456789, loc)
d.Format(time.RFC3339)       // => "2024-02-29T13:45:07+09:00"
d.UTC().Format(time.RFC3339) // => "2024-02-29T04:45:07Z"
d.Format(time.RFC3339Nano)   // => "2024-02-29T13:45:07.123456789+09:00"
d.Format(time.DateOnly)      // => "2024-02-29"
```

## Contract

- `t` の Location のオフセットを `+09:00` の形で付ける。オフセットが 0（`time.UTC` や `FixedZone("", 0)`）のときだけ `Z`
- `RFC3339` は秒まで。ナノ秒は捨てる（四捨五入しない）。`RFC3339Nano` は末尾の 0 を除いた小数秒（`.12`）を出し、ナノ秒が 0 なら小数点ごと省く。固定桁が欲しければ `"2006-01-02T15:04:05.000Z07:00"`
- 年は 4 桁ゼロ埋め（`0999`）。5 桁以上や負の年はそのまま出る（`12345`、`-0001`）
- ゼロ値 `time.Time{}` は `0001-01-01T00:00:00Z`
- 実行環境のローカルタイムゾーンに依存しない（`t` が持つ Location だけで決まる）。`time.Now()` は `Local` なので、ホストの設定でオフセットが変わる
- 入力を変更しない純粋関数。panic しない
- 逆変換 `time.Parse(time.RFC3339, s)` は同じ瞬間を返す（`Equal` が `true`）が、返り値の Location は元の `*Location` ではない（オフセットだけを持つ固定ゾーン。`Local` のオフセットと一致すれば `Local`）

## Alternatives

- 元の Location で読み戻したいなら `time.ParseInLocation(time.RFC3339, s, loc)`
- 任意の書式は Go 独自のレイアウト `"2006-01-02 15:04:05"` で書く（`yyyy-MM-dd` は使えない）。日付だけ・時刻だけは `time.DateOnly` / `time.TimeOnly` / `time.DateTime`（Go 1.20）
- `encoding/json` は `time.Time` を `RFC3339Nano` で出力する（`"2024-02-29T13:45:07.123456789+09:00"`）
- UTC でも `+00:00` と書きたいなら `"2006-01-02T15:04:05-07:00"`（`Z07:00` の代わりに `-07:00`）

## Pitfalls

- オフセット表記が言語で違う。TypeScript（date-fns の `formatISO`）は実行環境のローカルオフセット、Python の `isoformat()` は UTC でも `+00:00`。Go は `t` の Location に従い、UTC だけ `Z`
- `RFC3339` はナノ秒を切り捨てるので、`Format` → `Parse` の往復で `Equal` が崩れる。往復させるなら `RFC3339Nano`
- レイアウトは `2006-01-02T15:04:05` の固定の参照時刻で書く。実際の日付を書くと全く別の書式になる
- `time.Parse` の返す Location は元と別物なので、`==` や `Location().String()` で比較しない。瞬間の比較は `Equal`

## Test

`examples/date-format-iso_test.go`
