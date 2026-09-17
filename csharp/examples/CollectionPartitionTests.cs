// カード collection-partition の Contract を検証するテスト
public class CollectionPartitionTests
{
    private static IEnumerable<int> Counting(List<int> log, int count)
    {
        for (var i = 0; i < count; i++)
        {
            log.Add(i);
            yield return i;
        }
    }

    [Fact(DisplayName = "lookup[true] と lookup[false] に順序を保ったまま振り分ける")]
    public void SplitsByPredicateInOrder()
    {
        var lookup = new[] { 1, 2, 3, 4, 5 }.ToLookup(n => n % 2 == 0);

        Assert.Equal(new[] { 2, 4 }, lookup[true]);
        Assert.Equal(new[] { 1, 3, 5 }, lookup[false]);
        Assert.Equal(2, lookup.Count);
    }

    [Fact(DisplayName = "入力を変更せず、要素は同じ参照")]
    public void DoesNotMutateInputAndKeepsReferences()
    {
        var a = new object();
        var b = new object();
        var input = new[] { a, b };

        var lookup = input.ToLookup(x => ReferenceEquals(x, a));

        Assert.Equal(new[] { a, b }, input);
        Assert.Same(a, lookup[true].Single());
        Assert.Same(b, lookup[false].Single());
    }

    [Fact(DisplayName = "即時評価。返る時点で入力をすべて読み終え、後から入力を変えても反映されない")]
    public void IsEagerAndSnapshotsInput()
    {
        var log = new List<int>();
        var lookup = Counting(log, 5).ToLookup(n => n % 2 == 0);
        Assert.Equal(5, log.Count);

        var list = new List<int> { 1 };
        var snapshot = list.ToLookup(n => n > 0);
        list.Add(2);
        Assert.Single(snapshot[true]);
    }

    [Fact(DisplayName = "述語は各要素につきちょうど 1 回、先頭から順に呼ばれる")]
    public void PredicateIsCalledOncePerElementInOrder()
    {
        var calls = new List<int>();

        new[] { 3, 1, 2 }.ToLookup(x =>
        {
            calls.Add(x);
            return x > 1;
        });

        Assert.Equal(new[] { 3, 1, 2 }, calls);
    }

    [Fact(DisplayName = "該当が無い側は例外にならず空の列。Count と Contains で存在を判定できる")]
    public void MissingSideIsEmptyWithoutException()
    {
        var lookup = new[] { 1, 3 }.ToLookup(n => n % 2 == 0);

        Assert.Empty(lookup[true]);
        Assert.Equal(new[] { 1, 3 }, lookup[false]);
        Assert.Equal(1, lookup.Count);
        Assert.False(lookup.Contains(true));
        Assert.True(lookup.Contains(false));
    }

    [Fact(DisplayName = "空のシーケンスは両方とも空")]
    public void EmptyReturnsBothEmpty()
    {
        var lookup = Array.Empty<int>().ToLookup(n => n > 0);

        Assert.Empty(lookup[true]);
        Assert.Empty(lookup[false]);
        Assert.Equal(0, lookup.Count);
    }

    [Fact(DisplayName = "source や述語が null なら呼び出し時に ArgumentNullException")]
    public void NullArgumentsThrowAtCallTime()
    {
        IEnumerable<int> source = null!;
        Assert.Throws<ArgumentNullException>(() => source.ToLookup(n => n > 0));
        Assert.Throws<ArgumentNullException>(() => new[] { 1 }.ToLookup((Func<int, bool>)null!));
    }

    [Fact(DisplayName = "MoreLINQ の Partition は (True, False) のタプルを即時評価で返す")]
    public void MoreLinqPartitionReturnsTrueFirst()
    {
        var log = new List<int>();

        var (even, odd) = MoreLinq.MoreEnumerable.Partition(Counting(log, 5), n => n % 2 == 0);

        Assert.Equal(5, log.Count);
        Assert.Equal(new[] { 0, 2, 4 }, even);
        Assert.Equal(new[] { 1, 3 }, odd);
    }
}
