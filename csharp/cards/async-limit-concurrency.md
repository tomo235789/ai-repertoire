---
id: async-limit-concurrency
lang: csharp
title: 非同期処理の同時実行数を制限する
tags: [同時実行数, 並列制限, セマフォ, 排他, concurrency-limit, semaphore, throttle-parallel, max-parallelism]
lib: stdlib
fn: SemaphoreSlim
since: "6.0"
verified: 2026-09-17
status: public
---

同時に走らせる非同期処理の数を `maxCount` までに抑える。コネクション数や同時リクエスト数の上限に合わせて並列度を絞るのに使う。**時間あたりの回数制限（レート制限）ではない**。`WaitAsync` で空きを待ち、`finally` で必ず `Release` する。

## Signature

```csharp
public SemaphoreSlim(int initialCount, int maxCount)
```

## Usage

```csharp
using System.Threading;
using System.Threading.Tasks;

using var sem = new SemaphoreSlim(2, 2); // 同時に 2 つまで
async Task<Item> FetchLimited(int id) {
    await sem.WaitAsync();
    try { return await FetchJsonAsync($"/api/items/{id}"); }
    finally { sem.Release(); }
}
var items = await Task.WhenAll(new[] { 1, 2, 3, 4 }.Select(FetchLimited)); // 常に 2 件以下しか同時に走らない
```

## Contract

- `WaitAsync()` は空き（`CurrentCount > 0`）があれば 1 減らして完了済みの `Task` を返す。空きが無ければ `Release()` が呼ばれるまで待つ
- `Release()` は 1 増やし（増やす前の値を返す）、待機者がいれば 1 つを起こす
- `maxCount` を指定すると、それを超える `Release()` は `SemaphoreFullException`。`maxCount` 無しのコンストラクタでは `initialCount` を超えて増え、その分だけ同時実行数が増える
- `initialCount` が負か `maxCount` より大きいと `ArgumentOutOfRangeException`
- `WaitAsync(CancellationToken)` はキャンセルで `OperationCanceledException` を投げ、permit は取得しない。呼び出し時点でキャンセル済みなら `TaskCanceledException`（`OperationCanceledException` の派生）
- `WaitAsync(timeout)` は空きが得られたら `true`、時間切れなら `false` を返す（例外にならない）
- `Dispose()` 後の `WaitAsync` / `Release` は `ObjectDisposedException`。`Dispose` は待機中の `Task` を完了させず、その後の挙動は未定義（永久に待ち続けることがある）。待機者がいる間は `Dispose` しない
- スレッド安全。1 つのインスタンスを複数のタスクから共有して使う

## Alternatives

- `Parallel.ForEachAsync(items, new ParallelOptions { MaxDegreeOfParallelism = 2 }, async (item, ct) => ...)`（.NET 6）なら `WaitAsync` / `Release` を書かずに済む
- 同時に 1 つだけ（排他）なら `new SemaphoreSlim(1, 1)`。`lock` は `await` をまたげない
- 待機に制限時間を付けるなら `WaitAsync(TimeSpan)` の戻り値を見るか `WaitAsync(CancellationToken)`
- 依存を増やせず順序も気にしないなら `Chunk`（カード collection-chunk）で分けて `Task.WhenAll` を順に回す（バッチ内は並列、バッチ間は直列）
- 「1 秒に N 回まで」のような時間あたりの回数制限なら `System.Threading.RateLimiting`（.NET 7）の `SlidingWindowRateLimiter` / `TokenBucketRateLimiter`

## Pitfalls

- `Release()` を忘れると空きが戻らず、以後の `WaitAsync()` は永久に待つ。必ず `try { ... } finally { sem.Release(); }` で囲む。`using` は `Dispose` するだけで `Release` はしない
- TypeScript（es-toolkit の `Semaphore`）は余分な `release()` を無視し、Python の `asyncio.Semaphore` は上限が崩れる。C# は `maxCount` を渡せば `SemaphoreFullException` で検出できる（Python の `BoundedSemaphore` 相当）。対応関係が不安なら必ず `maxCount` を渡す
- es-toolkit は FIFO を保証するが、`SemaphoreSlim` は保証しない。再開順に依存するロジックを書かない
- `sem.Wait()`（同期版）を `async` メソッドで呼ぶとスレッドを占有しデッドロックの原因になる。`await sem.WaitAsync()` を使う
- 同時実行数を 2 に絞っても、処理が速ければ 1 秒に何十回でも呼べる。API のレート制限（回数 / 時間）を守る目的には使えない

## Test

`examples/AsyncLimitConcurrencyTests.cs`
