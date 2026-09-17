using System.ComponentModel.DataAnnotations;
using System.Diagnostics;
using Polly;
using Polly.Retry;

public class AsyncRetryTests
{
    private static ResiliencePipeline Build(Action<RetryStrategyOptions>? configure = null)
    {
        var options = new RetryStrategyOptions { Delay = TimeSpan.Zero };
        configure?.Invoke(options);
        return new ResiliencePipelineBuilder().AddRetry(options).Build();
    }

    [Fact(DisplayName = "失敗したら再実行し、成功した回の値を返す")]
    public async Task RetriesUntilSuccess()
    {
        var calls = 0;
        var result = await Build().ExecuteAsync(ct =>
        {
            calls++;
            if (calls < 3) throw new InvalidOperationException("fail");
            return ValueTask.FromResult("ok" + calls);
        });
        Assert.Equal("ok3", result);
        Assert.Equal(3, calls);
    }

    [Fact(DisplayName = "既定は MaxRetryAttempts 3・Delay 2 秒・Constant・ジッター無し")]
    public void DefaultOptions()
    {
        var options = new RetryStrategyOptions();
        Assert.Equal(3, options.MaxRetryAttempts);
        Assert.Equal(TimeSpan.FromSeconds(2), options.Delay);
        Assert.Equal(DelayBackoffType.Constant, options.BackoffType);
        Assert.False(options.UseJitter);
    }

    [Fact(DisplayName = "MaxRetryAttempts は再試行の回数で、合計は +1 回。上限に達したら最後の例外がそのまま投げられる")]
    public async Task ThrowsLastExceptionAfterMaxAttempts()
    {
        var thrown = new List<Exception>();
        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() => Build().ExecuteAsync(ct =>
        {
            var e = new InvalidOperationException("fail " + thrown.Count);
            thrown.Add(e);
            throw e;
        }).AsTask());
        Assert.Equal(4, thrown.Count);
        Assert.Same(thrown[^1], ex);
        Assert.Null(ex.InnerException);
    }

    [Fact(DisplayName = "MaxRetryAttempts が 1 未満だと Build 時に ValidationException")]
    public void InvalidMaxAttemptsFailsValidation()
    {
        Assert.Throws<ValidationException>(() => Build(o => o.MaxRetryAttempts = 0));
        Assert.Throws<ValidationException>(() => Build(o => o.MaxRetryAttempts = -1));
        Assert.Throws<ValidationException>(() => Build(o => o.Delay = TimeSpan.FromSeconds(-1)));
    }

    [Fact(DisplayName = "BackoffType ごとの待機時間と OnRetry の AttemptNumber（0 始まり）")]
    public async Task BackoffDelays()
    {
        async Task<List<(int Attempt, double Ms)>> Run(DelayBackoffType type)
        {
            var log = new List<(int, double)>();
            var pipeline = Build(o =>
            {
                o.Delay = TimeSpan.FromMilliseconds(1);
                o.BackoffType = type;
                o.OnRetry = a => { log.Add((a.AttemptNumber, a.RetryDelay.TotalMilliseconds)); return default; };
            });
            await Assert.ThrowsAsync<InvalidOperationException>(() => pipeline.ExecuteAsync(ct => throw new InvalidOperationException("x")).AsTask());
            return log;
        }
        Assert.Equal([(0, 1), (1, 1), (2, 1)], await Run(DelayBackoffType.Constant));
        Assert.Equal([(0, 1), (1, 2), (2, 4)], await Run(DelayBackoffType.Exponential));
        Assert.Equal([(0, 1), (1, 2), (2, 3)], await Run(DelayBackoffType.Linear));
    }

    [Fact(DisplayName = "Delay の分だけ実際に待ち、最後の試行のあとには待たない")]
    public async Task ActuallyWaitsBetweenAttempts()
    {
        var pipeline = Build(o => { o.Delay = TimeSpan.FromMilliseconds(10); o.MaxRetryAttempts = 2; });
        var sw = Stopwatch.StartNew();
        await Assert.ThrowsAsync<InvalidOperationException>(() => pipeline.ExecuteAsync(ct => throw new InvalidOperationException("x")).AsTask());
        Assert.InRange(sw.ElapsedMilliseconds, 18, 500);
    }

    [Fact(DisplayName = "ShouldHandle の既定は OperationCanceledException 以外のすべての例外")]
    public async Task DefaultShouldHandleSkipsCancellation()
    {
        var calls = 0;
        await Assert.ThrowsAsync<OperationCanceledException>(() => Build().ExecuteAsync(ct => { calls++; throw new OperationCanceledException(); }).AsTask());
        Assert.Equal(1, calls);
        calls = 0;
        await Assert.ThrowsAsync<ArgumentException>(() => Build(o => o.MaxRetryAttempts = 1).ExecuteAsync(ct => { calls++; throw new ArgumentException("bug"); }).AsTask());
        Assert.Equal(2, calls);
    }

    [Fact(DisplayName = "ShouldHandle に合わない例外は再試行せずその場で投げる")]
    public async Task UnhandledExceptionIsNotRetried()
    {
        var calls = 0;
        var pipeline = Build(o => o.ShouldHandle = new PredicateBuilder().Handle<TimeoutException>());
        await Assert.ThrowsAsync<InvalidOperationException>(() => pipeline.ExecuteAsync(ct => { calls++; throw new InvalidOperationException("nope"); }).AsTask());
        Assert.Equal(1, calls);
        calls = 0;
        var lambda = Build(o => { o.MaxRetryAttempts = 2; o.ShouldHandle = args => ValueTask.FromResult(args.Outcome.Exception is TimeoutException); });
        await Assert.ThrowsAsync<TimeoutException>(() => lambda.ExecuteAsync(ct => { calls++; throw new TimeoutException("t"); }).AsTask());
        Assert.Equal(3, calls);
    }

    [Fact(DisplayName = "待機中にキャンセルされると打ち切って OperationCanceledException を投げる")]
    public async Task CancellationDuringDelay()
    {
        var calls = 0;
        using var cts = new CancellationTokenSource();
        cts.CancelAfter(10);
        var pipeline = Build(o => { o.Delay = TimeSpan.FromSeconds(5); o.MaxRetryAttempts = 3; });
        var sw = Stopwatch.StartNew();
        await Assert.ThrowsAnyAsync<OperationCanceledException>(() => pipeline.ExecuteAsync(ct => { calls++; throw new InvalidOperationException("x"); }, cts.Token).AsTask());
        Assert.Equal(1, calls);
        Assert.True(sw.ElapsedMilliseconds < 1_000, $"elapsed {sw.ElapsedMilliseconds}ms");
    }

    [Fact(DisplayName = "戻り値で再試行を判定する HandleResult と、DelayGenerator・同期の Execute")]
    public async Task Alternatives()
    {
        var calls = 0;
        var typed = new ResiliencePipelineBuilder<int>().AddRetry(new RetryStrategyOptions<int>
        {
            Delay = TimeSpan.Zero,
            MaxRetryAttempts = 2,
            ShouldHandle = new PredicateBuilder<int>().HandleResult(r => r < 0),
        }).Build();
        Assert.Equal(2, await typed.ExecuteAsync(ct => { calls++; return ValueTask.FromResult(calls < 2 ? -1 : calls); }));

        var delays = new List<double>();
        var generated = Build(o =>
        {
            o.MaxRetryAttempts = 2;
            o.DelayGenerator = a => new ValueTask<TimeSpan?>(TimeSpan.FromMilliseconds(a.AttemptNumber));
            o.OnRetry = a => { delays.Add(a.RetryDelay.TotalMilliseconds); return default; };
        });
        await Assert.ThrowsAsync<InvalidOperationException>(() => generated.ExecuteAsync(ct => throw new InvalidOperationException("x")).AsTask());
        Assert.Equal([0, 1], delays);

        var syncCalls = 0;
        Assert.Throws<InvalidOperationException>(() => Build(o => o.MaxRetryAttempts = 1).Execute(() => { syncCalls++; throw new InvalidOperationException("x"); }));
        Assert.Equal(2, syncCalls);
    }
}
