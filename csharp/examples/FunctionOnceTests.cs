using System.Collections.Concurrent;

public class FunctionOnceTests
{
    [Fact(DisplayName = "最初の .Value で 1 回だけ実行し、以後は同じ参照を返す")]
    public void RunsOnceAndReturnsSameInstance()
    {
        var calls = 0;
        var init = new Lazy<object>(() => { calls++; return new object(); });
        Assert.False(init.IsValueCreated);
        Assert.Equal(0, calls);
        var a = init.Value;
        var b = init.Value;
        Assert.Same(a, b);
        Assert.Equal(1, calls);
        Assert.True(init.IsValueCreated);
    }

    [Fact(DisplayName = "既定モードは複数スレッドから同時に読んでも 1 回だけ実行される")]
    public void DefaultModeIsThreadSafe()
    {
        var calls = 0;
        var lazy = new Lazy<object>(() => { Interlocked.Increment(ref calls); Thread.Sleep(10); return new object(); });
        var results = new ConcurrentBag<object>();
        var threads = Enumerable.Range(0, 8).Select(_ => new Thread(() => results.Add(lazy.Value))).ToList();
        threads.ForEach(t => t.Start());
        threads.ForEach(t => t.Join());
        Assert.Equal(1, calls);
        Assert.Single(results.Distinct());
    }

    [Fact(DisplayName = "例外もキャッシュされ、以後は valueFactory を呼ばずに同じ例外を投げ続ける")]
    public void ExceptionIsCached()
    {
        var calls = 0;
        var lazy = new Lazy<int>(() => { calls++; throw new InvalidOperationException("boom"); });
        var first = Assert.Throws<InvalidOperationException>(() => lazy.Value);
        var second = Assert.Throws<InvalidOperationException>(() => lazy.Value);
        Assert.Same(first, second);
        Assert.Equal(1, calls);
        Assert.False(lazy.IsValueCreated);
    }

    [Fact(DisplayName = "PublicationOnly は例外をキャッシュせず次回再実行する")]
    public void PublicationOnlyRetriesAfterException()
    {
        var calls = 0;
        var lazy = new Lazy<int>(() => { if (++calls == 1) throw new InvalidOperationException("boom"); return 42; }, LazyThreadSafetyMode.PublicationOnly);
        Assert.Throws<InvalidOperationException>(() => lazy.Value);
        Assert.Equal(42, lazy.Value);
        Assert.Equal(2, calls);
    }

    [Fact(DisplayName = "PublicationOnly は同時アクセスで valueFactory が複数回走り得るが公開される値は 1 つ")]
    public void PublicationOnlyMayRunFactoryMultipleTimes()
    {
        var calls = 0;
        var lazy = new Lazy<object>(() => { Interlocked.Increment(ref calls); Thread.Sleep(10); return new object(); }, LazyThreadSafetyMode.PublicationOnly);
        var results = new ConcurrentBag<object>();
        var threads = Enumerable.Range(0, 8).Select(_ => new Thread(() => results.Add(lazy.Value))).ToList();
        threads.ForEach(t => t.Start());
        threads.ForEach(t => t.Join());
        Assert.True(calls >= 1);
        Assert.Single(results.Distinct());
    }

    [Fact(DisplayName = "None モードでも例外はキャッシュされる")]
    public void NoneModeCachesException()
    {
        var calls = 0;
        var lazy = new Lazy<int>(() => { calls++; throw new InvalidOperationException("boom"); }, LazyThreadSafetyMode.None);
        Assert.Throws<InvalidOperationException>(() => lazy.Value);
        Assert.Throws<InvalidOperationException>(() => lazy.Value);
        Assert.Equal(1, calls);
    }

    [Fact(DisplayName = "valueFactory 内で自身の Value を読むと InvalidOperationException")]
    public void RecursionThrows()
    {
        Lazy<int>? lazy = null;
        lazy = new Lazy<int>(() => lazy!.Value + 1);
        Assert.Throws<InvalidOperationException>(() => lazy.Value);
    }

    [Fact(DisplayName = "valueFactory が null なら ArgumentNullException")]
    public void NullFactoryThrows()
    {
        Assert.Throws<ArgumentNullException>(() => new Lazy<int>((Func<int>)null!));
    }

    [Fact(DisplayName = "Lazy<Task<T>> で非同期の初期化を 1 回にできる")]
    public async Task LazyTaskSharesFirstTask()
    {
        var calls = 0;
        var lazy = new Lazy<Task<int>>(async () => { calls++; await Task.Delay(5); return 7; });
        var results = await Task.WhenAll(lazy.Value, lazy.Value, lazy.Value);
        Assert.Equal([7, 7, 7], results);
        Assert.Equal(1, calls);
    }
}
