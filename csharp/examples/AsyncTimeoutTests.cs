public class AsyncTimeoutTests
{
    [Fact(DisplayName = "制限時間内に完了すればその結果を返す")]
    public async Task ReturnsResultWhenInTime()
    {
        var result = await Task.Run(async () => { await Task.Delay(5); return 42; }).WaitAsync(TimeSpan.FromSeconds(1));
        Assert.Equal(42, result);
    }

    [Fact(DisplayName = "元の Task が先に失敗すればその例外がそのまま伝わる")]
    public async Task PropagatesOriginalException()
    {
        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            Task.Run<int>(async () => { await Task.Delay(5); throw new InvalidOperationException("inner"); }).WaitAsync(TimeSpan.FromSeconds(1)));
        Assert.Equal("inner", ex.Message);
    }

    [Fact(DisplayName = "制限時間を過ぎると TimeoutException を投げる")]
    public async Task ThrowsTimeoutException()
    {
        await Assert.ThrowsAsync<TimeoutException>(() => Task.Delay(500).WaitAsync(TimeSpan.FromMilliseconds(10)));
    }

    [Fact(DisplayName = "タイムアウトしても元の Task は止まらず最後まで走る")]
    public async Task OriginalTaskKeepsRunning()
    {
        var tcs = new TaskCompletionSource<int>();
        var inner = tcs.Task;
        await Assert.ThrowsAsync<TimeoutException>(() => inner.WaitAsync(TimeSpan.FromMilliseconds(10)));
        Assert.Equal(TaskStatus.WaitingForActivation, inner.Status);
        tcs.SetResult(5);
        Assert.Equal(5, await inner);
    }

    [Fact(DisplayName = "CancellationToken 版はキャンセルで TaskCanceledException、時間切れが先なら TimeoutException")]
    public async Task CancellationTokenOverloads()
    {
        using var cts = new CancellationTokenSource();
        var waiting = Task.Delay(500).WaitAsync(cts.Token);
        cts.Cancel();
        await Assert.ThrowsAsync<TaskCanceledException>(() => waiting);

        using var cts2 = new CancellationTokenSource();
        var both = Task.Delay(500).WaitAsync(TimeSpan.FromSeconds(5), cts2.Token);
        cts2.Cancel();
        await Assert.ThrowsAsync<TaskCanceledException>(() => both);

        using var cts3 = new CancellationTokenSource();
        await Assert.ThrowsAsync<TimeoutException>(() => Task.Delay(500).WaitAsync(TimeSpan.FromMilliseconds(10), cts3.Token));
    }

    [Fact(DisplayName = "完了済みの Task には完了済みの Task が返り、無限のタイムアウトは元の Task の完了を待つ")]
    public async Task CompletedTaskAndInfiniteTimeout()
    {
        var done = Task.FromResult(1);
        var wrapped = done.WaitAsync(TimeSpan.FromSeconds(1));
        Assert.True(wrapped.IsCompletedSuccessfully);
        Assert.Equal(1, await wrapped);

        var failed = Task.FromException<int>(new InvalidOperationException("inner"));
        var ex = await Assert.ThrowsAsync<InvalidOperationException>(() => failed.WaitAsync(TimeSpan.FromSeconds(1)));
        Assert.Equal("inner", ex.Message);

        var tcs = new TaskCompletionSource<int>();
        var infinite = tcs.Task.WaitAsync(Timeout.InfiniteTimeSpan);
        await Task.Delay(20);
        Assert.False(infinite.IsCompleted);
        tcs.SetResult(7);
        Assert.Equal(7, await infinite);
    }

    [Fact(DisplayName = "TimeSpan.Zero は未完了なら即座に TimeoutException、完了済みなら結果を返す")]
    public async Task ZeroTimeout()
    {
        Assert.Equal(3, await Task.FromResult(3).WaitAsync(TimeSpan.Zero));
        await Assert.ThrowsAsync<TimeoutException>(() => Task.Delay(50).WaitAsync(TimeSpan.Zero));
    }

    [Fact(DisplayName = "範囲外のタイムアウトは呼び出し時に ArgumentOutOfRangeException")]
    public async Task InvalidTimeoutThrowsSynchronously()
    {
        var task = Task.Delay(10);
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => task.WaitAsync(TimeSpan.FromMilliseconds(-2)));
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => task.WaitAsync(TimeSpan.FromDays(60)));
    }

    [Fact(DisplayName = "CancelAfter で処理自体を止める、WhenAny の旧イディオム")]
    public async Task Alternatives()
    {
        using var cts = new CancellationTokenSource();
        cts.CancelAfter(10);
        await Assert.ThrowsAsync<TaskCanceledException>(() => Task.Delay(5_000, cts.Token));

        var inner = Task.Delay(500);
        var finished = await Task.WhenAny(inner, Task.Delay(10));
        Assert.NotSame(inner, finished);
    }
}
