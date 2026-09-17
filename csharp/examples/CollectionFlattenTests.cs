// カード collection-flatten の Contract を検証するテスト
public class CollectionFlattenTests
{
    private static IEnumerable<int[]> Counting(List<int> log, int count)
    {
        for (var i = 0; i < count; i++)
        {
            log.Add(i);
            yield return new[] { i, i };
        }
    }

    [Fact(DisplayName = "外側の順に各内側の順で 1 段だけ開く")]
    public void FlattensOneLevelInOrder()
    {
        var nested = new[] { new[] { 1, 2 }, Array.Empty<int>(), new[] { 3 } };

        Assert.Equal(new[] { 1, 2, 3 }, nested.SelectMany(x => x));
    }

    [Fact(DisplayName = "開くのは 1 段だけ。要素がさらに IEnumerable でも開かない")]
    public void DoesNotFlattenDeeper()
    {
        var nested = new[] { new object[] { 1, new[] { 2, 3 } } };

        var flat = nested.SelectMany(x => x).ToList();

        Assert.Equal(2, flat.Count);
        Assert.Equal(1, flat[0]);
        Assert.Equal(new[] { 2, 3 }, Assert.IsType<int[]>(flat[1]));
    }

    [Fact(DisplayName = "入力を変更せず、要素は同じ参照")]
    public void DoesNotMutateInputAndKeepsReferences()
    {
        var a = new object();
        var inner = new[] { a };
        var input = new[] { inner };

        var flat = input.SelectMany(x => x).ToList();

        Assert.Same(inner, input[0]);
        Assert.Same(a, inner[0]);
        Assert.Same(a, flat[0]);
    }

    [Fact(DisplayName = "遅延評価。取り出した分だけ外側を読み進める")]
    public void IsLazy()
    {
        var log = new List<int>();
        var flat = Counting(log, 5).SelectMany(x => x);
        Assert.Empty(log);

        using var e = flat.GetEnumerator();
        e.MoveNext();
        Assert.Equal(new[] { 0 }, log);
    }

    [Fact(DisplayName = "selector は各外側要素につきちょうど 1 回呼ばれ、添字付き・resultSelector 付きのオーバーロードがある")]
    public void SelectorIsCalledOncePerOuterElementAndOverloadsExist()
    {
        var calls = 0;
        new[] { new[] { 1 }, new[] { 2 } }.SelectMany(x =>
        {
            calls++;
            return x;
        }).ToList();
        Assert.Equal(2, calls);

        var withIndex = new[] { new[] { "a", "b" }, new[] { "c" } }.SelectMany((x, i) => x.Select(s => s + i));
        Assert.Equal(new[] { "a0", "b0", "c1" }, withIndex);

        var withResult = new[] { new[] { 1, 2 }, new[] { 3 } }.SelectMany(x => x, (outer, n) => n * outer.Length);
        Assert.Equal(new[] { 2, 4, 3 }, withResult);
    }

    [Fact(DisplayName = "空、または空しか含まないシーケンスは空を返す")]
    public void EmptyReturnsEmpty()
    {
        Assert.Empty(Array.Empty<int[]>().SelectMany(x => x));
        Assert.Empty(new[] { Array.Empty<int>(), Array.Empty<int>() }.SelectMany(x => x));
    }

    [Fact(DisplayName = "引数が null なら呼び出し時に ArgumentNullException。selector が null を返すと列挙時に NullReferenceException")]
    public void NullHandling()
    {
        IEnumerable<int[]> source = null!;
        Assert.Throws<ArgumentNullException>(() => source.SelectMany(x => x));
        Assert.Throws<ArgumentNullException>(() => new[] { new[] { 1 } }.SelectMany((Func<int[], IEnumerable<int>>)null!));

        var deferred = new[] { 1 }.SelectMany(_ => (IEnumerable<int>)null!);
        Assert.Throws<NullReferenceException>(() => deferred.ToList());
    }

    [Fact(DisplayName = "string は IEnumerable<char> なので文字に分解される")]
    public void StringsAreFlattenedIntoChars()
    {
        Assert.Equal(new[] { 'a', 'b', 'c' }, new[] { "ab", "c" }.SelectMany(s => s));
    }
}
