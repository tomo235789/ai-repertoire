using System.Diagnostics;

public class AsyncSleepTests
{
    [Fact(DisplayName = "指定ミリ秒後に完了する")]
    public async Task CompletesAfterDelay()
    {
        var sw = Stopwatch.StartNew();
        await Task.Delay(10);
        Assert.True(sw.ElapsedMilliseconds >= 9, $"elapsed {sw.ElapsedMilliseconds}ms");
        sw.Restart();
        await Task.Delay(TimeSpan.FromMilliseconds(10));
        Assert.True(sw.ElapsedMilliseconds >= 9, $"elapsed {sw.ElapsedMilliseconds}ms");
    }

    [Fact(DisplayName = "待っている間はスレッドを占有せず、複数の待機が並行して進む")]
    public async Task DoesNotBlockOtherWork()
    {
        // 実時間の上限で判定すると CI ランナーの負荷で落ちるので、
        // 「呼び出し直後は未完了（ブロックしない）」と「短い待機が長い待機より先に終わる」で検証する
        var longer = Task.Delay(500);
        var shorter = Task.Delay(10);
        Assert.False(longer.IsCompleted);
        await shorter;
        Assert.False(longer.IsCompleted);  // 直列に待っていたらここで完了しているはず
        await longer;
    }

    [Fact(DisplayName = "キャンセルすると TaskCanceledException で打ち切られ、元のトークンが分かる")]
    public async Task CancellationThrowsTaskCanceled()
    {
        using var cts = new CancellationTokenSource();
        var waiting = Task.Delay(10_000, cts.Token);
        cts.Cancel();
        var ex = await Assert.ThrowsAsync<TaskCanceledException>(() => waiting);
        Assert.IsAssignableFrom<OperationCanceledException>(ex);
        Assert.Equal(cts.Token, ex.CancellationToken);
        Assert.True(waiting.IsCanceled);
    }

    [Fact(DisplayName = "呼び出し時点でキャンセル済みのトークンでも同じくキャンセル状態になる")]
    public async Task PreCancelledTokenCancelsImmediately()
    {
        var waiting = Task.Delay(10_000, new CancellationToken(canceled: true));
        Assert.Equal(TaskStatus.Canceled, waiting.Status);
        await Assert.ThrowsAsync<TaskCanceledException>(() => waiting);
    }

    [Fact(DisplayName = "CancelAfter で途中キャンセルすると残りを待たない")]
    public async Task CancelAfterCutsWaitShort()
    {
        using var cts = new CancellationTokenSource();
        cts.CancelAfter(10);
        var sw = Stopwatch.StartNew();
        await Assert.ThrowsAsync<TaskCanceledException>(() => Task.Delay(5_000, cts.Token));
        Assert.True(sw.ElapsedMilliseconds < 1_000, $"elapsed {sw.ElapsedMilliseconds}ms");
    }

    [Fact(DisplayName = "0 は完了済みの Task を返す")]
    public void ZeroReturnsCompletedTask()
    {
        Assert.True(Task.Delay(0).IsCompletedSuccessfully);
        Assert.True(Task.Delay(TimeSpan.Zero).IsCompletedSuccessfully);
    }

    [Fact(DisplayName = "-1 は無限に待ち、-2 以下は ArgumentOutOfRangeException")]
    public async Task NegativeValues()
    {
        Assert.False(Task.Delay(-1).IsCompleted);
        Assert.False(Task.Delay(Timeout.InfiniteTimeSpan).IsCompleted);
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => Task.Delay(-2));
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => Task.Delay(TimeSpan.FromMilliseconds(-2)));
    }

    [Fact(DisplayName = "TimeSpan 版は約 49 日を超える値を受け付けない")]
    public async Task TooLongTimeSpanThrows()
    {
        await Assert.ThrowsAsync<ArgumentOutOfRangeException>(() => Task.Delay(TimeSpan.FromDays(60)));
    }

    [Fact(DisplayName = "TimeProvider 版と PeriodicTimer も待機に使える")]
    public async Task Alternatives()
    {
        await Task.Delay(TimeSpan.FromMilliseconds(5), TimeProvider.System);
        using var timer = new PeriodicTimer(TimeSpan.FromMilliseconds(5));
        Assert.True(await timer.WaitForNextTickAsync());
    }
}
