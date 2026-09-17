// カード collection-zip の Contract を検証するテスト
public class CollectionZipTests
{
    private static IEnumerable<int> Counting(List<int> log, int count)
    {
        for (var i = 0; i < count; i++)
        {
            log.Add(i);
            yield return i;
        }
    }

    [Fact(DisplayName = "同じ位置どうしを順序を保ったままタプルにする")]
    public void PairsElementsByPosition()
    {
        var pairs = new[] { "a", "b", "c" }.Zip(new[] { 1, 2, 3 }).ToList();

        Assert.Equal(new[] { ("a", 1), ("b", 2), ("c", 3) }, pairs);
    }

    [Fact(DisplayName = "入力を変更せず、タプルの要素は同じ参照")]
    public void DoesNotMutateInputAndKeepsReferences()
    {
        var a = new object();
        var b = new object();
        var first = new[] { a };
        var second = new[] { b };

        var pair = first.Zip(second).Single();

        Assert.Equal(new[] { a }, first);
        Assert.Equal(new[] { b }, second);
        Assert.Same(a, pair.First);
        Assert.Same(b, pair.Second);
    }

    [Fact(DisplayName = "遅延評価。タプル 1 つ分ずつ両方の入力を読み進める")]
    public void IsLazy()
    {
        var log1 = new List<int>();
        var log2 = new List<int>();
        var zipped = Counting(log1, 5).Zip(Counting(log2, 5));
        Assert.Empty(log1);
        Assert.Empty(log2);

        using var e = zipped.GetEnumerator();
        e.MoveNext();
        Assert.Single(log1);
        Assert.Single(log2);
    }

    [Fact(DisplayName = "最も短い入力で打ち切る。second が短いと first から 1 要素余分に読まれる")]
    public void TruncatesToShortestAndOverReadsFirstByOne()
    {
        Assert.Equal(2, new[] { 1, 2, 3 }.Zip(new[] { "a", "b" }).Count());

        var log = new List<int>();
        Counting(log, 5).Zip(new[] { "a" }).ToList();
        Assert.Equal(new[] { 0, 1 }, log);

        log.Clear();
        new[] { "a" }.Zip(Counting(log, 5)).ToList();
        Assert.Equal(new[] { 0 }, log);
    }

    [Fact(DisplayName = "3 引数版は 3 要素タプル、resultSelector 版は結果を直接作る")]
    public void SupportsThreeSequencesAndResultSelector()
    {
        var triples = new[] { 1, 2 }.Zip(new[] { "a", "b", "c" }, new[] { true, false }).ToList();
        Assert.Equal(new[] { (1, "a", true), (2, "b", false) }, triples);

        var joined = new[] { 1, 2 }.Zip(new[] { "a", "b" }, (n, s) => $"{n}{s}");
        Assert.Equal(new[] { "1a", "2b" }, joined);
    }

    [Fact(DisplayName = "どちらかが空なら空を返す")]
    public void EmptyInputReturnsEmpty()
    {
        Assert.Empty(Array.Empty<int>().Zip(new[] { 1 }));
        Assert.Empty(new[] { 1 }.Zip(Array.Empty<int>()));
    }

    [Fact(DisplayName = "引数が null なら呼び出し時に ArgumentNullException")]
    public void NullArgumentsThrowAtCallTime()
    {
        IEnumerable<int> nul = null!;
        Assert.Throws<ArgumentNullException>(() => nul.Zip(new[] { 1 }));
        Assert.Throws<ArgumentNullException>(() => new[] { 1 }.Zip(nul));
    }
}
