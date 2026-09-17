---
id: async-timeout
lang: csharp
title: Promise に制限時間を設ける
tags: [タイムアウト, 制限時間, 打ち切り, 時間切れ, timeout, deadline, time-limit]
lib: stdlib
fn: Task.WaitAsync
since: "6.0"
verified: 2026-09-17
status: public
---

`Task` が制限時間内に終わらなければ `TimeoutException` で失敗する `Task` を返す。外部 API 呼び出しの待ちすぎ防止に使う。

## Signature

```csharp
public Task<TResult> WaitAsync(TimeSpan timeout)
```

## Usage

```csharp
using System;
using System.Threading.Tasks;

try {
    var data = await FetchJsonAsync("/api/items").WaitAsync(TimeSpan.FromSeconds(3));
    // => 3 秒以内に終わればその結果
} catch (TimeoutException) {
    Console.WriteLine("3 秒以内に終わらなかった");
}
```

## Contract

- 元の `Task` が `timeout` 以内に完了すればその結果を返す。先に失敗すればその例外がそのまま伝わる
- `timeout` を過ぎても完了しなければ `TimeoutException` を投げる。**元の `Task` は止まらない**。処理は裏で最後まで走り、結果や例外は捨てられる
- `CancellationToken` 版 `WaitAsync(token)` / `WaitAsync(timeout, token)` はキャンセルで `TaskCanceledException`。両方渡して時間切れが先なら `TimeoutException`
- 既に完了している `Task` に呼ぶと完了済みの `Task` が返り、結果や例外はそのまま。`Timeout.InfiniteTimeSpan` を渡すと制限時間なしで元の `Task` の完了を待つ（`TimeoutException` にはならない）
- `TimeSpan.Zero` は未完了なら即座に `TimeoutException`
- `timeout` が `-1` ミリ秒（無限）未満か `uint.MaxValue - 1` ミリ秒を超えると呼び出し時に `ArgumentOutOfRangeException`

## Alternatives

- 処理そのものを止めたいなら `CancellationTokenSource.CancelAfter(timeout)` のトークンを処理に渡す。`WaitAsync` は待つのをやめるだけ
- .NET 5 以前は `Task.WhenAny(task, Task.Delay(timeout))` で先に終わった方を見るイディオム（`Delay` のタイマーが残る）
- `ValueTask` には無い。`.AsTask().WaitAsync(...)`
- 同期的に待つなら `task.Wait(timeout)`（`bool` を返す。`async` の中では使わない）

## Pitfalls

- TypeScript（es-toolkit の `withTimeout`）と同じく元の処理はキャンセルされない。Python の `asyncio.timeout` は中の処理をキャンセルするので意味論が違う。副作用のある処理（書き込み・送金）に付けると「タイムアウトしたのに完了している」状態が起こり得る
- 元の `Task` が後で失敗しても、`WaitAsync` 側で捨てられるので気付けない。ログが要るなら `ContinueWith` などで観測する
- `TimeoutException` と `TaskCanceledException` は別の型。制限時間とキャンセルの両方を使うなら両方 `catch` する
- `HttpClient` の既定タイムアウト（100 秒）のように、ライブラリが独自の `TimeoutException` や `TaskCanceledException` を投げることがある。`WaitAsync` の例外と混同しない

## Test

`examples/AsyncTimeoutTests.cs`
