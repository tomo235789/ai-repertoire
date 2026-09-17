---
id: async-sleep
lang: go
title: 指定ミリ秒待つ
tags: [待機, スリープ, 遅延, 一時停止, sleep, delay, wait]
lib: stdlib
fn: time.Sleep
since: "1.0"
verified: 2026-09-17
status: public
---

現在の goroutine を指定時間だけ止める。ポーリング間隔やリトライ前の待機、テストのタイミング調整に使う。キャンセルが要るなら `select` で `context` と組み合わせる。

## Signature

```go
func Sleep(d Duration)
```

## Usage

```go
import ("context"; "time")

time.Sleep(500 * time.Millisecond) // 500ms 止まる（他の goroutine は動き続ける）

// 途中で止めたいなら context と組み合わせる
select {
case <-time.After(10 * time.Second):
case <-ctx.Done(): // キャンセルされたら待たずに抜ける
}
```

## Contract

- 少なくとも `d` の間、現在の goroutine を止める。他の goroutine は動き続ける。戻り値は無い
- `d` が 0 以下なら即座に返る。panic しない
- **`time.Sleep` 自体はキャンセルできない**。`context` で打ち切るには `select` で `time.After(d)` と `ctx.Done()` を待つ。キャンセル時は `ctx.Err()` が `context.Canceled`（期限なら `context.DeadlineExceeded`）
- `Duration` はナノ秒単位の `int64`。`time.Sleep(500)` は 500 ナノ秒で、ミリ秒ではない
- 実際の待ち時間は `d` 以上で、OS のタイマー精度のぶん長くなる

## Alternatives

- 制限時間付きで別の処理を待つならカード async-timeout（`context.WithTimeout`）
- 一定間隔の繰り返しは `time.NewTicker`
- Go 1.23 以降、`time.After` のタイマーは参照が無くなれば GC されるので、`NewTimer` + `Stop` に書き換える必要は無い

## Pitfalls

- 単位が言語で違う。TypeScript（es-toolkit の `delay(500)`）はミリ秒、Python（`asyncio.sleep(0.5)`）は秒、Go は **ナノ秒単位の `Duration`**。`500 * time.Millisecond` のように単位を掛ける
- `time.Sleep` は `context` を見ない。長い待ちを `Sleep` で書くとシャットダウンやリクエストのキャンセルに反応できない。秒単位以上の待ちは `select` の形にする
- テストで実時間を待つと遅く不安定になる。待ち時間を引数にして短くするか、`testing/synctest`（Go 1.25）で仮想時間を使う
- goroutine の中で `Sleep` しても呼び出し元は止まらない。待つなら `sync.WaitGroup` などで合流する

## Test

`examples/async-sleep_test.go`
