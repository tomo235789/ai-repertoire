---
id: async-timeout
lang: go
title: Promise に制限時間を設ける
tags: [タイムアウト, 制限時間, 打ち切り, 時間切れ, timeout, deadline, time-limit, context]
lib: stdlib
fn: context.WithTimeout
since: "1.7"
verified: 2026-09-17
status: public
---

制限時間付きの `context.Context` を作り、`ctx` を受け取る処理に渡す。期限が来ると `ctx.Done()` が閉じ、`ctx.Err()` が `context.DeadlineExceeded` になる。外部 API 呼び出しの待ちすぎ防止に使う。

## Signature

```go
func WithTimeout(parent Context, timeout time.Duration) (Context, CancelFunc)
```

## Usage

```go
import ("context"; "errors"; "fmt"; "time")

ctx, cancel := context.WithTimeout(context.Background(), 3*time.Second)
defer cancel() // 早く終わっても必ず呼ぶ

data, err := fetchJSON(ctx, "/api/items") // ctx を見る関数に渡す
if errors.Is(err, context.DeadlineExceeded) {
	fmt.Println("3 秒以内に終わらなかった")
}
```

## Contract

- `timeout` の経過、`cancel()` の呼び出し、親の終了のうち最初のもので `ctx.Done()` が閉じる。`ctx.Err()` は期限なら `context.DeadlineExceeded`、`cancel()` や親のキャンセルなら `context.Canceled`。それまでは `nil`
- 判定は `errors.Is(err, context.DeadlineExceeded)`。`DeadlineExceeded` は変数なので `==` でも比較できる
- `timeout` が 0 以下なら、返された時点で既に `DeadlineExceeded`
- 親の期限の方が早ければ親の期限で `DeadlineExceeded` になる。`ctx.Deadline()` で締め切りを確認できる
- **処理は自動では止まらない**。`ctx` を受け取る関数（`net/http`、`database/sql` など）は自分で `ctx.Done()` を見て中断する。`ctx` を見ない goroutine はタイムアウト後も走り続ける
- `cancel` を呼ばないとタイマーなどのリソースが親の終了まで解放されない。`defer cancel()` を必ず書く（`go vet` の `lostcancel` が警告する）
- `context.Cause(ctx)` は既定で `Err()` と同じ。`WithTimeoutCause` で理由を差し替えられる（Go 1.21）

## Alternatives

- 絶対時刻で指定するなら `context.WithDeadline`
- 理由を持たせるなら `context.WithTimeoutCause(parent, d, errors.New("slow api"))`。`ctx.Err()` は `DeadlineExceeded` のまま、`context.Cause(ctx)` で理由が取れる
- `ctx` を受け取らない処理に制限時間を付けるなら、結果チャネルと `ctx.Done()` を `select` で待つ。処理自体は止まらない
- goroutine の集合をまとめてキャンセルするなら `errgroup.WithContext`（カード async-limit-concurrency）

## Pitfalls

- 中断の意味論が 3 言語で違う。TypeScript（es-toolkit の `withTimeout`）は元の処理を止めず、Python（`asyncio.timeout`）は中の処理をキャンセルするが、Go は **協調的**。`ctx` を渡し、かつ渡した先が見ていて初めて止まる
- `cancel()` を先に呼ぶと `Err()` は `Canceled` で、`DeadlineExceeded` にならない
- ライブラリはエラーを包んで返すことが多いので、判定は `==` ではなく `errors.Is`
- タイムアウトしたのに処理が完了している状態が起こりうる。副作用のある処理（書き込み・送金など）は結果の扱いを決めておく

## Test

`examples/async-timeout_test.go`
