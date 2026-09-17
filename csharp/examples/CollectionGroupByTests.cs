// カード collection-group-by の Contract を検証するテスト
public class CollectionGroupByTests
{
    private static IEnumerable<int> Counting(List<int> log, int count)
    {
        for (var i = 0; i < count; i++)
        {
            log.Add(i);
            yield return i;
        }
    }

    [Fact(DisplayName = "グループはキーの初出順、各グループの中は元の出現順")]
    public void GroupsInFirstAppearanceOrder()
    {
        var items = new[] { (type: "b", n: 1), (type: "a", n: 2), (type: "b", n: 3) };

        var groups = items.GroupBy(x => x.type).ToList();

        Assert.Equal(new[] { "b", "a" }, groups.Select(g => g.Key));
        Assert.Equal(new[] { 1, 3 }, groups[0].Select(x => x.n));
        Assert.Equal(new[] { 2 }, groups[1].Select(x => x.n));
    }

    [Fact(DisplayName = "入力を変更せず、要素は同じ参照。各グループは何度でも列挙できる")]
    public void DoesNotMutateInputAndGroupsAreReenumerable()
    {
        var a = new object();
        var b = new object();
        var input = new[] { a, b };

        var group = input.GroupBy(_ => 0).Single();

        Assert.Equal(new[] { a, b }, input);
        Assert.Same(a, group.First());
        Assert.Equal(2, group.Count());
        Assert.Equal(2, group.Count());
    }

    [Fact(DisplayName = "遅延評価だが最初のグループを取り出す時点で入力をすべて読み切り、列挙のたびに再計算する")]
    public void IsDeferredButReadsAllOnFirstMoveNext()
    {
        var log = new List<int>();
        var groups = Counting(log, 5).GroupBy(x => x % 2);
        Assert.Empty(log);

        using var e = groups.GetEnumerator();
        e.MoveNext();
        Assert.Equal(new[] { 0, 1, 2, 3, 4 }, log);

        log.Clear();
        groups.ToList();
        groups.ToList();
        Assert.Equal(10, log.Count);
    }

    [Fact(DisplayName = "keySelector は各要素につきちょうど 1 回、先頭から順に呼ばれる")]
    public void KeySelectorIsCalledOncePerElementInOrder()
    {
        var calls = new List<int>();

        new[] { 3, 1, 3 }.GroupBy(x =>
        {
            calls.Add(x);
            return x;
        }).ToList();

        Assert.Equal(new[] { 3, 1, 3 }, calls);
    }

    [Fact(DisplayName = "キーの比較は既定で Equals。比較器を渡すと大文字小文字を無視できる")]
    public void UsesDefaultComparerOrGivenComparer()
    {
        var words = new[] { "a", "A" };

        Assert.Equal(2, words.GroupBy(w => w).Count());
        Assert.Single(words.GroupBy(w => w, StringComparer.OrdinalIgnoreCase));
    }

    [Fact(DisplayName = "null キーのグループが 1 つできる")]
    public void NullKeyFormsOneGroup()
    {
        var items = new[] { (k: (string?)null, v: 1), (k: (string?)"a", v: 2), (k: (string?)null, v: 3) };

        var groups = items.GroupBy(x => x.k).ToList();

        Assert.Equal(2, groups.Count);
        Assert.Null(groups[0].Key);
        Assert.Equal(new[] { 1, 3 }, groups[0].Select(x => x.v));
    }

    [Fact(DisplayName = "空のシーケンスは空を返す")]
    public void EmptyReturnsEmpty()
    {
        Assert.Empty(Array.Empty<int>().GroupBy(x => x));
    }

    [Fact(DisplayName = "source や keySelector が null なら呼び出し時に ArgumentNullException")]
    public void NullArgumentsThrowAtCallTime()
    {
        IEnumerable<int> source = null!;
        Assert.Throws<ArgumentNullException>(() => source.GroupBy(x => x));
        Assert.Throws<ArgumentNullException>(() => new[] { 1 }.GroupBy((Func<int, int>)null!));
    }
}
