// カード collection-dedup-by-key の Contract を検証するテスト
public class CollectionDedupByKeyTests
{
    private sealed class Box
    {
        public int Id { get; init; }
    }

    private static IEnumerable<int> Counting(List<int> log, int count)
    {
        for (var i = 0; i < count; i++)
        {
            log.Add(i);
            yield return i;
        }
    }

    [Fact(DisplayName = "順序を保ち、同じキーの要素は最初に出現したものを残す")]
    public void KeepsFirstOccurrenceInOrder()
    {
        var users = new[] { (id: 1, name: "a"), (id: 2, name: "b"), (id: 1, name: "c") };

        var result = users.DistinctBy(u => u.id).ToList();

        Assert.Equal(new[] { (id: 1, name: "a"), (id: 2, name: "b") }, result);
    }

    [Fact(DisplayName = "入力を変更せず、返り値の要素は同じ参照")]
    public void DoesNotMutateInputAndKeepsReferences()
    {
        var first = new Box { Id = 1 };
        var second = new Box { Id = 2 };
        var dup = new Box { Id = 1 };
        var input = new[] { first, second, dup };

        var result = input.DistinctBy(b => b.Id).ToList();

        Assert.Equal(new[] { first, second, dup }, input);
        Assert.Same(first, result[0]);
        Assert.Same(second, result[1]);
    }

    [Fact(DisplayName = "遅延評価。取り出した分だけ入力を読み、列挙のたびに読み直す")]
    public void IsLazyAndReenumeratesInput()
    {
        var log = new List<int>();
        var result = Counting(log, 10).DistinctBy(x => x % 2);
        Assert.Empty(log);

        using var e = result.GetEnumerator();
        e.MoveNext();
        Assert.Equal(new[] { 0 }, log);

        log.Clear();
        result.ToList();
        result.ToList();
        Assert.Equal(20, log.Count);
    }

    [Fact(DisplayName = "keySelector は各要素につきちょうど 1 回、先頭から順に呼ばれる")]
    public void KeySelectorIsCalledOncePerElementInOrder()
    {
        var calls = new List<int>();

        new[] { 3, 1, 3, 2 }.DistinctBy(x =>
        {
            calls.Add(x);
            return x;
        }).ToList();

        Assert.Equal(new[] { 3, 1, 3, 2 }, calls);
    }

    [Fact(DisplayName = "キーの比較は既定で Equals。比較器を渡すと大文字小文字を無視できる")]
    public void UsesDefaultComparerOrGivenComparer()
    {
        var words = new[] { "a", "A", "b" };

        Assert.Equal(new[] { "a", "A", "b" }, words.DistinctBy(w => w));
        Assert.Equal(new[] { "a", "b" }, words.DistinctBy(w => w, StringComparer.OrdinalIgnoreCase));
    }

    [Fact(DisplayName = "Equals を実装しないクラスをキーにすると参照比較になり除去されない")]
    public void ClassKeyWithoutEqualsIsComparedByReference()
    {
        var items = new[] { 1, 1 };

        Assert.Equal(2, items.DistinctBy(x => new Box { Id = x }).Count());
        Assert.Single(items.DistinctBy(x => (x, x)));
    }

    [Fact(DisplayName = "null キーの要素も 1 つだけ残る")]
    public void NullKeyIsKeptOnce()
    {
        var items = new[] { (k: (string?)null, v: 1), (k: (string?)"a", v: 2), (k: (string?)null, v: 3) };

        Assert.Equal(new[] { 1, 2 }, items.DistinctBy(x => x.k).Select(x => x.v));
    }

    [Fact(DisplayName = "空のシーケンスは空を返す")]
    public void EmptyReturnsEmpty()
    {
        Assert.Empty(Array.Empty<int>().DistinctBy(x => x));
    }

    [Fact(DisplayName = "source や keySelector が null なら呼び出し時に ArgumentNullException")]
    public void NullArgumentsThrowAtCallTime()
    {
        IEnumerable<int> source = null!;
        Assert.Throws<ArgumentNullException>(() => source.DistinctBy(x => x));
        Assert.Throws<ArgumentNullException>(() => new[] { 1 }.DistinctBy((Func<int, int>)null!));
    }
}
