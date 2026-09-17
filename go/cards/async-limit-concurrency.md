---
id: async-limit-concurrency
lang: go
title: 非同期処理の同時実行数を制限する
tags: [同時実行数, 並列制限, セマフォ, goroutine, concurrency-limit, semaphore, errgroup, rate-limit]
lib: golang.org/x/sync
fn: errgroup.Group.SetLimit
since: "0.7"
verified: 2026-09-17
status: public
---

同時に走らせる goroutine の数を `n` までに抑え、最初のエラーで残りをキャンセルする。API のレート制限やコネクション数の上限に合わせて並列度を絞るのに使う。

## Signature

```go
func (g *Group) SetLimit(n int)
```

## Usage

```go
import ("context"; "golang.org/x/sync/errgroup")

g, ctx := errgroup.WithContext(context.Background())
g.SetLimit(2) // 同時に 2 つまで
for _, id := range []int{1, 2, 3, 4} {
	g.Go(func() error { return fetchItem(ctx, id) }) // 枠が空くまでブロック
}
err := g.Wait() // => 全部終わるまで待ち、最初のエラー（無ければ nil）
// => 常に 2 件以下しか同時に fetchItem されない
```

## Contract

- `SetLimit(n)` 以後、同時に走る goroutine を `n` 個までにする。`Go` は枠が空くまで **呼び出し側をブロック** する。`TryGo` は枠が無ければ起動せず `false` を返す
- `Wait` は全 goroutine の終了を待ち、**最初に非 nil を返した** 関数のエラーを返す（`Go` に渡した順ではなく、返した順）。他のエラーは捨てられる。全部 `nil` なら `nil`。`Wait` を 2 回呼んでも同じエラー
- `WithContext` で作ると、最初のエラーで `ctx` がキャンセルされる。`ctx.Err()` は `context.Canceled`、`context.Cause(ctx)` はそのエラー。**`Wait` が返るときも `ctx` はキャンセルされる**（エラーが無くても）
- `ctx` がキャンセルされても、その後の `Go` は goroutine を起動する。各関数が `ctx.Done()` を見て早期に返す必要がある
- `n < 0` は無制限、`n == 0` は新規起動を禁止（`TryGo` が `false`）。ゼロ値の `Group` は無制限でキャンセルもしない
- goroutine が動いている間の `SetLimit` は **非対応**。`n >= 0` を渡すと panic する。`n < 0`（無制限へ）や、無制限の状態から呼んだ場合は現在の実装（v0.23.0）では panic しないが、後者は動作中の goroutine の終了で `Wait` が返らなくなりうる。どちらも当てにしない
- goroutine の中の panic は捕捉されず、プロセスごと落ちる（v0.23.0）。関数の中で `recover` して `error` に変換する

## Alternatives

- 結果を集めたいなら、事前に確保したスライスにインデックスで書く（別要素への書き込みは競合しない）
- エラー伝播が要らず制限だけなら `golang.org/x/sync/semaphore.Weighted` か容量 `n` のチャネル
- 制限も要らず待つだけなら `sync.WaitGroup`（Go 1.25 の `wg.Go(f)`）

## Pitfalls

- TypeScript（es-toolkit の `Semaphore`）や Python（`asyncio.Semaphore`）は permit の取得・解放を自分で書くが、`errgroup` は `Go` の中だけで完結し解放忘れが起きない。代わりに **`Go` がブロックする** ので、投入ループの途中で `ctx.Err()` を確認しないと、キャンセル後も残りを全部投入してしまう
- 最初のエラー以外は捨てられる。全部のエラーが欲しいなら各関数で `sync.Mutex` 付きのスライスに集めて `errors.Join` する
- `WithContext` の `ctx` は `Wait` の後でキャンセル済みなので、`Wait` の後の処理に使い回さない
- `SetLimit` は最初の `Go` の前に呼ぶ。動作中に変えるのは非対応で、panic するか `Wait` が返らなくなる
- Go 1.22 未満ではループ変数を関数に渡す前にコピーする（`id := id`）

## Test

`examples/async-limit-concurrency_test.go`
