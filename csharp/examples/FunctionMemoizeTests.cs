using System.Collections.Concurrent;

public class FunctionMemoizeTests
{
    [Fact(DisplayName = "同じキーの 2 回目は valueFactory を呼ばず保存した値を返す")]
    public void CachesPerKey()
    {
        var cache = new ConcurrentDictionary<int, double>();
        var calls = 0;
        double Area(int r) => cache.GetOrAdd(r, key => { calls++; return Math.PI * key * key; });
        var first = Area(2);
        var second = Area(2);
        Area(3);
        Assert.Equal(first, second);
        Assert.Equal(2, calls);
    }

    [Fact(DisplayName = "複数の引数はタプルにまとめると値で比較される")]
    public void TupleKeysCompareByValue()
    {
        var cache = new ConcurrentDictionary<(int, string), int>();
        var calls = 0;
        int F(int a, string b) => cache.GetOrAdd((a, b), k => { calls++; return k.Item1 + k.Item2.Length; });
        F(1, "ab");
        F(1, "ab");
        F(2, "ab");
        Assert.Equal(2, calls);
    }

    [Fact(DisplayName = "比較は EqualityComparer<TKey>.Default で、コンストラクタで差し替えられる")]
    public void UsesDefaultComparerUnlessOverridden()
    {
        var byNaN = new ConcurrentDictionary<double, int>();
        byNaN.GetOrAdd(double.NaN, 1);
        Assert.Equal(1, byNaN.GetOrAdd(double.NaN, 2));
        var ignoreCase = new ConcurrentDictionary<string, int>(StringComparer.OrdinalIgnoreCase);
        ignoreCase.GetOrAdd("A", 1);
        Assert.Equal(1, ignoreCase.GetOrAdd("a", 2));
    }

    [Fact(DisplayName = "valueFactory が例外を投げると保存されず、次回また呼ばれる")]
    public void ExceptionIsNotCached()
    {
        var cache = new ConcurrentDictionary<int, int>();
        var calls = 0;
        int Compute(int k) { calls++; if (calls == 1) throw new InvalidOperationException("boom"); return k * 10; }
        Assert.Throws<InvalidOperationException>(() => cache.GetOrAdd(1, Compute));
        Assert.Empty(cache);
        Assert.Equal(10, cache.GetOrAdd(1, Compute));
        Assert.Equal(2, calls);
    }

    [Fact(DisplayName = "同時に同じキーで呼ぶと valueFactory は複数回実行され得るが、保存されるのは 1 つで全員同じ値を受け取る")]
    public void ConcurrentFactoriesMayRunMultipleTimes()
    {
        var cache = new ConcurrentDictionary<int, object>();
        var calls = 0;
        using var barrier = new Barrier(4);
        var results = new ConcurrentBag<object>();
        var threads = Enumerable.Range(0, 4).Select(_ => new Thread(() =>
            results.Add(cache.GetOrAdd(1, _ => { Interlocked.Increment(ref calls); barrier.SignalAndWait(); return new object(); })))).ToList();
        threads.ForEach(t => t.Start());
        threads.ForEach(t => t.Join());
        Assert.Equal(4, calls);
        Assert.Single(cache);
        Assert.Single(results.Distinct());
    }

    [Fact(DisplayName = "値を Lazy<T> にすると計算は厳密に 1 回になる")]
    public void LazyValueRunsFactoryOnce()
    {
        var cache = new ConcurrentDictionary<int, Lazy<object>>();
        var calls = 0;
        var results = new ConcurrentBag<object>();
        var threads = Enumerable.Range(0, 8).Select(_ => new Thread(() =>
            results.Add(cache.GetOrAdd(1, _ => new Lazy<object>(() => { Interlocked.Increment(ref calls); Thread.Sleep(10); return new object(); })).Value))).ToList();
        threads.ForEach(t => t.Start());
        threads.ForEach(t => t.Join());
        Assert.Equal(1, calls);
        Assert.Single(results.Distinct());
    }

    [Fact(DisplayName = "null の戻り値も値として保存される")]
    public void NullResultIsCached()
    {
        var cache = new ConcurrentDictionary<int, string?>();
        var calls = 0;
        string? F(int k) => cache.GetOrAdd(k, _ => { calls++; return null; });
        Assert.Null(F(1));
        Assert.Null(F(1));
        Assert.Equal(1, calls);
        Assert.Single(cache);
    }

    [Fact(DisplayName = "key や valueFactory が null なら ArgumentNullException、Clear と TryRemove で消せる")]
    public void NullArgumentsAndRemoval()
    {
        var cache = new ConcurrentDictionary<string, int>();
        Assert.Throws<ArgumentNullException>(() => cache.GetOrAdd(null!, k => 1));
        Assert.Throws<ArgumentNullException>(() => cache.GetOrAdd("a", (Func<string, int>)null!));
        cache.GetOrAdd("a", 1);
        Assert.True(cache.TryRemove("a", out _));
        cache.GetOrAdd("b", 2);
        cache.Clear();
        Assert.Empty(cache);
    }

    [Fact(DisplayName = "値そのものや追加引数付きの多重定義")]
    public void OtherOverloads()
    {
        var cache = new ConcurrentDictionary<int, string>();
        Assert.Equal("a", cache.GetOrAdd(1, "a"));
        Assert.Equal("a", cache.GetOrAdd(1, "b"));
        Assert.Equal("2x", cache.GetOrAdd(2, static (k, arg) => k + arg, "x"));
    }
}
