public class AsyncLimitConcurrencyTests
{
    [Fact(DisplayName = "同時実行数が maxCount を超えない")]
    public async Task LimitsConcurrency()
    {
        using var sem = new SemaphoreSlim(2, 2);
        var current = 0;
        var peak = 0;
        async Task Work()
        {
            await sem.WaitAsync();
            try
            {
                var now = Interlocked.Increment(ref current);
                int seen;
                while ((seen = peak) < now && Interlocked.CompareExchange(ref peak, now, seen) != seen) { }
                await Task.Delay(10);
            }
            finally
            {
                Interlocked.Decrement(ref current);
                sem.Release();
            }
        }
        await Task.WhenAll(Enumerable.Range(0, 6).Select(_ => Work()));
        Assert.Equal(2, peak);
        Assert.Equal(2, sem.CurrentCount);
    }

    [Fact(DisplayName = "空きがあれば WaitAsync は即座に完了し CurrentCount が減る。無ければ Release まで待つ")]
    public async Task WaitAsyncAndRelease()
    {
        using var sem = new SemaphoreSlim(1, 1);
        var first = sem.WaitAsync();
        Assert.True(first.IsCompletedSuccessfully);
        Assert.Equal(0, sem.CurrentCount);
        var second = sem.WaitAsync();
        Assert.False(second.IsCompleted);
        Assert.Equal(0, sem.Release());
        await second;
        Assert.True(second.IsCompletedSuccessfully);
        Assert.Equal(0, sem.CurrentCount);
    }

    [Fact(DisplayName = "maxCount を超える Release は SemaphoreFullException、maxCount 無しなら増え続ける")]
    public void ExtraReleaseBehaviour()
    {
        using var bounded = new SemaphoreSlim(1, 1);
        Assert.Throws<SemaphoreFullException>(() => bounded.Release());
        Assert.Equal(1, bounded.CurrentCount);
        using var unbounded = new SemaphoreSlim(1);
        unbounded.Release();
        Assert.Equal(2, unbounded.CurrentCount);
    }

    [Fact(DisplayName = "initialCount が負か maxCount より大きいと ArgumentOutOfRangeException")]
    public void InvalidCountsThrow()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new SemaphoreSlim(-1));
        Assert.Throws<ArgumentOutOfRangeException>(() => new SemaphoreSlim(3, 2));
    }

    [Fact(DisplayName = "待機中のキャンセルは OperationCanceledException で permit は取得しない")]
    public async Task CancellationWhileWaiting()
    {
        using var sem = new SemaphoreSlim(0, 1);
        using var cts = new CancellationTokenSource();
        var waiting = sem.WaitAsync(cts.Token);
        cts.Cancel();
        await Assert.ThrowsAnyAsync<OperationCanceledException>(() => waiting);
        Assert.Equal(0, sem.CurrentCount);
        sem.Release();
        Assert.Equal(1, sem.CurrentCount);
        using var pre = new SemaphoreSlim(1, 1);
        await Assert.ThrowsAsync<TaskCanceledException>(() => pre.WaitAsync(new CancellationToken(canceled: true)));
        Assert.Equal(1, pre.CurrentCount);
    }

    [Fact(DisplayName = "WaitAsync(timeout) は取得できれば true、時間切れなら false")]
    public async Task TimeoutOverloadReturnsBool()
    {
        using var empty = new SemaphoreSlim(0, 1);
        Assert.False(await empty.WaitAsync(10));
        using var available = new SemaphoreSlim(1, 1);
        Assert.True(await available.WaitAsync(TimeSpan.FromMilliseconds(10)));
        Assert.Equal(0, available.CurrentCount);
    }

    [Fact(DisplayName = "Dispose 後の WaitAsync / Release は ObjectDisposedException")]
    public async Task DisposedBehaviour()
    {
        var sem = new SemaphoreSlim(0, 1);
        var waiting = sem.WaitAsync();
        Assert.False(waiting.IsCompleted);
        sem.Release();
        await waiting; // 待機者を完了させてから Dispose する（待機者がいる間に Dispose した後の挙動は未定義）
        sem.Dispose();

        await Assert.ThrowsAsync<ObjectDisposedException>(() => sem.WaitAsync());
        Assert.Throws<ObjectDisposedException>(() => sem.Release());
    }

    [Fact(DisplayName = "例外が出ても finally で Release され空きが戻る")]
    public async Task FinallyReleases()
    {
        using var sem = new SemaphoreSlim(1, 1);
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
        {
            await sem.WaitAsync();
            try { throw new InvalidOperationException("x"); }
            finally { sem.Release(); }
        });
        Assert.Equal(1, sem.CurrentCount);
    }

    [Fact(DisplayName = "Parallel.ForEachAsync でも並列度を絞れる")]
    public async Task ParallelForEachAsyncAlternative()
    {
        var current = 0;
        var peak = 0;
        await Parallel.ForEachAsync(Enumerable.Range(0, 6), new ParallelOptions { MaxDegreeOfParallelism = 2 }, async (_, ct) =>
        {
            var now = Interlocked.Increment(ref current);
            int seen;
            while ((seen = peak) < now && Interlocked.CompareExchange(ref peak, now, seen) != seen) { }
            await Task.Delay(10, ct);
            Interlocked.Decrement(ref current);
        });
        Assert.InRange(peak, 1, 2);
    }
}
