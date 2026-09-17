---
id: async-sleep
lang: csharp
title: 指定ミリ秒待つ
tags: [待機, スリープ, 遅延, 一時停止, sleep, delay, wait]
lib: stdlib
fn: Task.Delay
since: "6.0"
verified: 2026-09-17
status: public
---

指定ミリ秒後に完了する `Task` を返す。ポーリング間隔やリトライ前の待機、テストのタイミング調整に使う。スレッドを止めずに待つので、`await` で使う。

## Signature

```csharp
public static Task Delay(int millisecondsDelay, CancellationToken cancellationToken)
```

## Usage

```csharp
using System.Threading;
using System.Threading.Tasks;

await Task.Delay(500); // 500ms 待つ（スレッドは解放される）
using var cts = new CancellationTokenSource();
var waiting = Task.Delay(10_000, cts.Token);
cts.Cancel();
try { await waiting; } catch (TaskCanceledException) { /* 待機が打ち切られた */ }
```

## Contract

- `millisecondsDelay` 後に完了する `Task` を返す。値は返さない。待っている間スレッドは解放され、他の処理が動く
- `cancellationToken` がキャンセルされると待機を打ち切り、`Task` は `Canceled` 状態になる。`await` すると `TaskCanceledException`（`OperationCanceledException` の派生）が投げられ、`CancellationToken` プロパティで元のトークンが分かる。呼び出し時点でキャンセル済みでも同じ
- `0` を渡すと完了済みの `Task` を返す（実時間の待機は無い）
- `-1`（`Timeout.Infinite` / `Timeout.InfiniteTimeSpan`）は無限に待つ。`-2` 以下は `ArgumentOutOfRangeException`
- `TimeSpan` 版は `uint.MaxValue - 1` ミリ秒（約 49 日）を超える値も `ArgumentOutOfRangeException`
- 引数はミリ秒。`TimeSpan` 版 `Task.Delay(TimeSpan.FromMilliseconds(500))` も同じ挙動

## Alternatives

- 同期コード（スレッド）で待つなら `Thread.Sleep(ms)`。`async` メソッドの中では使わない（スレッドを占有し、UI やリクエスト処理を止める）
- 別の非同期処理に制限時間を付けるなら `Task.WaitAsync`（カード async-timeout）
- テストで時間を進めたいなら `Task.Delay(TimeSpan, TimeProvider)`（.NET 8）に `FakeTimeProvider` を渡す
- 定期実行は `PeriodicTimer`（.NET 6）

## Pitfalls

- 引数はミリ秒。Python の `asyncio.sleep(0.5)` を移植するなら `Task.Delay(500)`。`Task.Delay(0.5)` は `int` に暗黙変換されずコンパイルエラー
- `await` を付け忘れると `Task` が作られるだけで待たない（警告 CS4014）
- `Thread.Sleep` を `async` の中で呼ぶとイベントループ相当のスレッドが止まる。必ず `await Task.Delay`
- キャンセル時の例外は `TaskCanceledException` だが、`catch (OperationCanceledException)` で受けるのが一般的（`SemaphoreSlim.WaitAsync` など他の API は基底の `OperationCanceledException` を投げる）

## Test

`examples/AsyncSleepTests.cs`
