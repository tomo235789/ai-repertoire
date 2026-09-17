---
id: date-diff-days
lang: go
title: 2 つの日付の暦日差を求める
tags: [日付差, 日数差, 経過日数, 暦日, diff, days-between, difference, calendar-days]
lib: stdlib
fn: time.Time.Sub
since: "1.0"
verified: 2026-09-17
status: public
---

時刻を無視して、2 つの日付が暦の上で何日離れているかを求める。各自のローカル日付（年・月・日）を UTC の 0 時として組み立て直してから `Sub` するので、DST や Location のオフセットに左右されない。残り日数の表示や「同じ日か」の判定に使う。

## Signature

```go
func (t Time) Sub(u Time) Duration
```

## Usage

```go
import "time"

func diffDays(later, earlier time.Time) int { // 各自のローカル日付を UTC の 0 時として組み立ててから引く
	l := time.Date(later.Year(), later.Month(), later.Day(), 0, 0, 0, 0, time.UTC)
	e := time.Date(earlier.Year(), earlier.Month(), earlier.Day(), 0, 0, 0, 0, time.UTC)
	return int(l.Sub(e).Hours() / 24)
}
loc, _ := time.LoadLocation("Asia/Tokyo")
diffDays(time.Date(2024, 3, 1, 0, 1, 0, 0, loc), time.Date(2024, 2, 29, 23, 59, 0, 0, loc)) // => 1
diffDays(time.Date(2024, 2, 29, 23, 59, 0, 0, loc), time.Date(2024, 3, 1, 0, 1, 0, 0, loc)) // => -1
```

## Contract

- 引数は「後の日付、前の日付」の順。結果は `later - earlier` の暦日差で、逆順なら負、同じ日なら `0`
- それぞれの Location でのローカル日付（年・月・日）だけを取り出し、UTC の 0 時として組み立ててから引くので、時刻は無視され差は必ず 24 時間の整数倍になる。2 分しか離れていなくても日付が変われば `1`
- Location の 0 時同士を直接 `Sub` すると DST 切替日は 23h / 25h になり、日付をスキップするゾーン（`Pacific/Apia` の 2011-12-30）では `math.Round` でも暦日差が 1 日ずれる。UTC で組み立て直す形ならどちらも正しい
- `Sub` は `Duration`（`int64` ナノ秒）を返し、約 292 年を超える差は `math.MaxInt64` に飽和する（`2000-01-01` と `2293-01-01` の差は飽和し、暦日差も誤る）
- 2 つの Location が違うと、それぞれのローカル日付で比べる。JST の `03-01 00:30` と UTC の `02-29 20:00` は実時間では JST の方が 4.5 時間早いが、ローカル日付が `03-01` と `02-29` なので `1`。UTC+14 と UTC−12 でローカル日付が同じなら、実時間が 1 日以上離れていても `0`。同じ基準で数えるなら先に `In(loc)` で揃える（揃えると `0`）
- 入力を変更しない純粋関数。panic しない。ゼロ値 `time.Time{}` も UTC の `0001-01-01` として扱える

## Alternatives

- 実時間で「丸 1 日が何回か」なら `int(later.Sub(earlier).Hours() / 24)`（ゼロ方向切り捨て）
- 同じ日かだけ知りたいなら `a.Date()` と `b.Date()` の 3 つ組を比べる（Location を揃えてから）
- 0 時への切り詰めはカード date-start-of-day
- 292 年を超える期間は `Unix()` 秒の差から計算する

## Pitfalls

- TypeScript（date-fns の `differenceInCalendarDays`）と Python の `(a.date() - b.date()).days` と同じ意味論。`differenceInDays` や `(a - b).days` は 24 時間単位で別物
- Location の 0 時同士を `Sub` して `Hours() / 24` を切り捨てると DST の 23 時間の日で `0` になる。`math.Round` で丸めても日付をスキップするゾーンではずれるので、暦日差は UTC で組み立て直してから引く
- `a.Truncate(24 * time.Hour)` で 0 時にするのは UTC 基準なので不正解（カード date-start-of-day）
- 別 Location の値を混ぜると結果の意味が曖昧になる。`In(time.UTC)` などで揃えてから渡す

## Test

`examples/date-diff-days_test.go`
