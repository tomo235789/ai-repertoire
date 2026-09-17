---
id: date-start-of-day
lang: go
title: 日付の時刻を 0 時に切り捨てる
tags: [日付の切り捨て, 0時, 日の始まり, 時刻除去, start-of-day, midnight, truncate-time, floor]
lib: stdlib
fn: time.Date
since: "1.0"
verified: 2026-09-17
status: public
---

`time.Time` の時刻部分を同じ Location の 00:00:00 にした新しい値を返す。日単位のキーやグルーピング、範囲検索の下限に使う。

## Signature

```go
func Date(year int, month Month, day, hour, min, sec, nsec int, loc *Location) Time
```

## Usage

```go
import "time"
func startOfDay(t time.Time) time.Time {
	y, m, d := t.Date()
	s := time.Date(y, m, d, 0, 0, 0, 0, t.Location())
	if s.Day() != d { // 0 時が存在しない日（DST 開始）は前日 23 時に正規化されるので、その日の最初の時刻へ進める
		s = s.Add(time.Hour)
	}
	return s
}
startOfDay(time.Date(2024, 2, 29, 13, 45, 7, 0, time.FixedZone("JST", 9*3600))) // => 2024-02-29 00:00:00 +0900 JST
```

## Contract

- `t` の Location の同じ日の 00:00:00.000000000 を返す。日付部分と Location はそのまま
- `time.Time` は値型なので入力は変わらない
- 冪等。結果をもう一度渡しても `Equal`
- 実行環境のローカルタイムゾーンに依存しない。`t` の Location だけで決まる。同じ瞬間でも Location が違えば別の瞬間になる（JST の 02-29 13:45 を `In(America/New_York)` にしてから丸めると 02-28 00:00 EST）
- ゼロ値 `time.Time{}` はゼロ値のまま（`Location()` は `UTC`）
- DST の開始が 0 時のゾーンでは 0 時が存在しない。存在しない時刻を `time.Date` がどちらのオフセットで解釈するかは **未規定**（現在の実装では `America/Sao_Paulo` の 2018-11-04 は前日 `2018-11-03 23:00:00 -03` になる）。上の実装は返った値の日付が前日にずれていたら 1 時間足すので、どちらに解釈されてもその日の最初の瞬間 `2018-11-04 01:00:00 -02` を返す。この補正が無いと前日を返す実装では冪等でなくなり、日付キーや範囲の下限に前日が混ざる
- panic しない（`time.Date` は `loc` が `nil` だと panic するが、`t.Location()` は `nil` を返さない）

## Alternatives

- 日付だけ欲しいなら `y, m, d := t.Date()`、日付キーの文字列なら `t.Format(time.DateOnly)`
- 特定のタイムゾーンでの 0 時が欲しいなら、先に `t.In(loc)` で変換してから丸める
- 日の終わりは `startOfDay(t).AddDate(0, 0, 1)` を上限に `Before` で比較する
- 月初は `time.Date(t.Year(), t.Month(), 1, 0, 0, 0, 0, t.Location())`

## Pitfalls

- `t.Truncate(24 * time.Hour)` は **ゼロ時刻からの絶対経過時間** で切るので、JST の 02-29 13:45 は `02-29 09:00 JST`（UTC の 0 時）になる。UTC 以外の Location では 0 時にならない
- TypeScript（date-fns の `startOfDay`）は実行環境のローカルで丸め、Python の `datetime.combine` は tzinfo を落とす罠があるが、Go は `t.Location()` を渡す限り Location を保つ。`time.UTC` を渡すと UTC の 0 時になり、JST の値からは 9 時間ずれる
- `time.Now()` の Location は `Local`。ホストの設定で日付の境界が変わるので、日付キーにするなら `In(loc)` で明示する
- `Unix()` を 86400 で割って丸める方法も UTC 基準で、`Truncate` と同じ問題がある

## Test

`examples/date-start-of-day_test.go`
