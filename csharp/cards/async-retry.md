---
id: async-retry
lang: csharp
title: 失敗した非同期処理を再試行する
tags: [再試行, リトライ, 失敗時の再実行, バックオフ, retry, backoff, resilience]
lib: Polly
fn: ResiliencePipelineBuilder.AddRetry
since: "8.0"
verified: 2026-09-17
status: public
---

例外を投げた非同期処理を待ってから再実行し、成功した値を返す。一時的なネットワークエラーへの対処に使う。Polly v8 の `ResiliencePipeline` に `RetryStrategyOptions` で組み込む。

## Signature

```csharp
public static ResiliencePipelineBuilder AddRetry(this ResiliencePipelineBuilder builder, RetryStrategyOptions options)
```

## Usage

```csharp
using Polly;
using Polly.Retry;

var pipeline = new ResiliencePipelineBuilder().AddRetry(new RetryStrategyOptions {
    MaxRetryAttempts = 3,                                                                 // 最大 3 回やり直す（合計 4 回まで）
    Delay = TimeSpan.FromMilliseconds(100), BackoffType = DelayBackoffType.Exponential, // 100, 200, 400ms
    ShouldHandle = new PredicateBuilder().Handle<HttpRequestException>(),                 // この例外のときだけ
}).Build();
var data = await pipeline.ExecuteAsync(async ct => await FetchJsonAsync("/api/items", ct));
// => 成功した回の値。4 回とも失敗したら最後の HttpRequestException がそのまま投げられる
```

## Contract

- コールバックを呼び、`ShouldHandle` に合う例外なら `Delay` だけ待って再実行する。正常に返った時点でその値を返す
- `MaxRetryAttempts` は **再試行の回数**。合計で最大 `MaxRetryAttempts + 1` 回呼ぶ。既定は `3`（合計 4 回）。`1` 未満はパイプライン構築時に `ValidationException`
- 既定の `Delay` は 2 秒、`BackoffType` は `Constant`、`UseJitter` は `false`。`Exponential` は `Delay × 2^n`（100, 200, 400ms...）、`Linear` は `Delay × (n + 1)`。最後の試行のあとには待たない
- `ShouldHandle` の既定は **`OperationCanceledException` 以外のすべての例外** を再試行する。`PredicateBuilder().Handle<T>()` か `args => ValueTask.FromResult(bool)` で絞る。合わない例外は再試行せずその場で投げる
- 上限に達したら **最後の試行の例外そのもの** を投げる。ラップされない
- `ExecuteAsync(callback, cancellationToken)` のトークンは各試行のコールバックに `ct` として渡され、待機中にキャンセルされると待機を打ち切って `OperationCanceledException`（`TaskCanceledException`）を投げる
- `OnRetry` は各再試行の待機前に呼ばれ、`AttemptNumber`（0 始まり）、`RetryDelay`、`Outcome.Exception` を読める

## Alternatives

- 戻り値で失敗を判定するなら `ResiliencePipelineBuilder<T>` と `RetryStrategyOptions<T>` の `ShouldHandle = new PredicateBuilder<T>().HandleResult(r => ...)`
- 待機時間を自前で決めるなら `DelayGenerator = args => new ValueTask<TimeSpan?>(...)`（`Retry-After` ヘッダー対応など）。`UseJitter = true` で待機時間にゆらぎを加える
- 1 回ごとに制限時間も付けたいなら `AddTimeout` を同じパイプラインに重ねる（カード async-timeout の `WaitAsync` をコールバック内で使ってもよい）
- 同期処理は `pipeline.Execute(() => ...)`。依存を増やせない場合は `for` ループと `try/catch` と `Task.Delay`

## Pitfalls

- TypeScript（es-toolkit の `retry`）は `retries` 省略時に無限に再試行し、Python の tenacity は既定で `RetryError` に包む。Polly は既定で 3 回・2 秒待ち、最後の例外をそのまま投げる
- `Delay` の既定 2 秒を忘れると、テストや短い処理で合計 6 秒待つ。テストでは `Delay = TimeSpan.Zero` にする
- `ShouldHandle` を省略すると `ArgumentException` や `NullReferenceException` などバグ由来の例外も再試行する。再試行に意味がある例外だけに絞る
- 冪等でない処理（送金・投稿）を再試行すると二重実行になり得る。リクエストが届いたあとにタイムアウトや切断で失敗した場合、例外の種類から「送信前に失敗した」とは判定できないので `ShouldHandle` では防げない。冪等キーを付けるか、再試行前に操作の状態を確認する

## Test

`examples/AsyncRetryTests.cs`
