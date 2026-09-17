// カード collection-take-while の Contract を検証するテスト
public class CollectionTakeWhileTests
{
    private static IEnumerable<int> Counting(List<int> log, int count)
    {
        for (var i = 0; i < count; i++)
        {
            log.Add(i);
            yield return i;
        }
    }

    [Fact(DisplayName = "先頭から述語が真の間だけ取り、最初に偽になった時点で打ち切る")]
    public void TakesPrefixWhileTrue()
    {
        Assert.Equal(new[] { 1, 2 }, new[] { 1, 2, 3, 1 }.TakeWhile(n => n < 3));
    }

    [Fact(DisplayName = "入力を変更せず、要素は同じ参照")]
    public void DoesNotMutateInputAndKeepsReferences()
    {
        var a = new object();
        var b = new object();
        var input = new[] { a, b };

        var result = input.TakeWhile(x => ReferenceEquals(x, a)).ToList();

        Assert.Equal(new[] { a, b }, input);
        Assert.Same(a, Assert.Single(result));
    }

    [Fact(DisplayName = "遅延評価。取り出した分だけ入力を読み進める")]
    public void IsLazy()
    {
        var log = new List<int>();
        var result = Counting(log, 10).TakeWhile(n => n < 5);
        Assert.Empty(log);

        using var e = result.GetEnumerator();
        e.MoveNext();
        Assert.Equal(new[] { 0 }, log);
    }

    [Fact(DisplayName = "述語は最初に偽を返した要素まで呼ばれ、それ以降は呼ばれない。その要素は入力から読み取られている")]
    public void PredicateStopsAtFirstFalseAndThatElementIsConsumed()
    {
        var calls = new List<int>();
        new[] { 1, 2, 3, 1 }.TakeWhile(n =>
        {
            calls.Add(n);
            return n < 3;
        }).ToList();
        Assert.Equal(new[] { 1, 2, 3 }, calls);

        var log = new List<int>();
        Counting(log, 10).TakeWhile(n => n < 2).ToList();
        Assert.Equal(new[] { 0, 1, 2 }, log);
    }

    [Fact(DisplayName = "添字付きのオーバーロードがある。SkipWhile と連結すると元に戻る")]
    public void IndexOverloadAndSkipWhile()
    {
        Assert.Equal(new[] { 5, 6 }, new[] { 5, 6, 7, 8 }.TakeWhile((_, i) => i < 2));

        var xs = new[] { 1, 2, 3, 1 };
        Assert.Equal(xs, xs.TakeWhile(n => n < 3).Concat(xs.SkipWhile(n => n < 3)));
    }

    [Fact(DisplayName = "すべて真なら全要素、先頭で偽なら空、空のシーケンスなら空")]
    public void BoundaryCases()
    {
        Assert.Equal(new[] { 1, 2 }, new[] { 1, 2 }.TakeWhile(_ => true));
        Assert.Empty(new[] { 1, 2 }.TakeWhile(_ => false));
        Assert.Empty(Array.Empty<int>().TakeWhile(_ => true));
    }

    [Fact(DisplayName = "引数が null なら呼び出し時に ArgumentNullException。述語の例外はそのまま伝播する")]
    public void NullArgumentsAndPredicateExceptions()
    {
        IEnumerable<int> source = null!;
        Assert.Throws<ArgumentNullException>(() => source.TakeWhile(_ => true));
        Assert.Throws<ArgumentNullException>(() => new[] { 1 }.TakeWhile((Func<int, bool>)null!));

        var deferred = new[] { 1 }.TakeWhile(_ => throw new InvalidOperationException("boom"));
        Assert.Throws<InvalidOperationException>(() => deferred.ToList());
    }
}
