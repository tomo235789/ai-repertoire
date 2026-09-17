// カード collection-sort-by の Contract を検証するテスト
using System.Globalization;

public class CollectionSortByTests
{
    private sealed class NotComparable
    {
    }

    private static IEnumerable<int> Counting(List<int> log, int count)
    {
        for (var i = 0; i < count; i++)
        {
            log.Add(i);
            yield return i;
        }
    }

    // 同じキーの要素の相対順が崩れていれば true
    private static bool HasInversion(IEnumerable<(int k, int n)> rows)
    {
        return rows.Zip(rows.Skip(1)).Any(p => p.First.k == p.Second.k && p.First.n > p.Second.n);
    }

    [Fact(DisplayName = "ThenBy を連ねると前のキーが等しいときだけ次のキーで比較する")]
    public void ThenByComparesNextKeyOnlyOnTie()
    {
        var rows = new[] { (g: "b", v: 2), (g: "a", v: 9), (g: "b", v: 1) };

        var sorted = rows.OrderBy(r => r.g).ThenBy(r => r.v).ToList();

        Assert.Equal(new[] { (g: "a", v: 9), (g: "b", v: 1), (g: "b", v: 2) }, sorted);
    }

    [Fact(DisplayName = "安定ソート。キーが等しい要素は昇順でも降順でも元の相対順を保つ")]
    public void IsStable()
    {
        var rows = new[] { (k: 1, n: "a"), (k: 0, n: "b"), (k: 1, n: "c"), (k: 0, n: "d") };

        Assert.Equal(new[] { "b", "d", "a", "c" }, rows.OrderBy(r => r.k).Select(r => r.n));
        Assert.Equal(new[] { "a", "c", "b", "d" }, rows.OrderByDescending(r => r.k).Select(r => r.n));

        var many = Enumerable.Range(0, 200).Select(i => (k: i % 3, n: i)).ToList();
        Assert.False(HasInversion(many.OrderBy(r => r.k).ToList()));
    }

    [Fact(DisplayName = "入力を変更せず、要素は同じ参照")]
    public void DoesNotMutateInputAndKeepsReferences()
    {
        var first = new NotComparable();
        var second = new NotComparable();
        var input = new[] { first, second };

        var sorted = input.OrderBy(x => ReferenceEquals(x, first) ? 1 : 0).ToList();

        Assert.Equal(new[] { first, second }, input);
        Assert.Same(second, sorted[0]);
        Assert.Same(first, sorted[1]);
    }

    [Fact(DisplayName = "遅延評価だが最初の要素を取り出す時点で入力をすべて読み切り、列挙のたびに再計算する")]
    public void IsDeferredButReadsAllOnFirstMoveNext()
    {
        var log = new List<int>();
        var sorted = Counting(log, 5).OrderBy(x => -x);
        Assert.Empty(log);

        using var e = sorted.GetEnumerator();
        e.MoveNext();
        Assert.Equal(5, log.Count);

        log.Clear();
        sorted.ToList();
        sorted.ToList();
        Assert.Equal(10, log.Count);
    }

    [Fact(DisplayName = "keySelector は各要素につきちょうど 1 回呼ばれる（比較のたびではない）")]
    public void KeySelectorIsCalledOncePerElement()
    {
        var calls = 0;

        Enumerable.Range(0, 50).Reverse().OrderBy(x =>
        {
            calls++;
            return x;
        }).ToList();

        Assert.Equal(50, calls);
    }

    [Fact(DisplayName = "OrderBy を 2 回連ねると後の OrderBy だけが効く")]
    public void SecondOrderByReplacesFirst()
    {
        var rows = new[] { (g: "b", v: 2), (g: "a", v: 9), (g: "b", v: 1) };

        var sorted = rows.OrderBy(r => r.g).OrderBy(r => r.v).Select(r => r.g + r.v);

        Assert.Equal(new[] { "b1", "b2", "a9" }, sorted);
    }

    [Fact(DisplayName = "null は最小として先頭、降順なら末尾。比較器を渡すと序数比較にできる")]
    public void NullIsSmallestAndComparerCanBeGiven()
    {
        var rows = new[] { (k: (string?)"b", n: 1), (k: (string?)null, n: 2), (k: (string?)"a", n: 3) };
        Assert.Equal(new[] { 2, 3, 1 }, rows.OrderBy(r => r.k).Select(r => r.n));
        Assert.Equal(new[] { 1, 3, 2 }, rows.OrderByDescending(r => r.k).Select(r => r.n));
        Assert.Equal(new[] { 3, 1, 2 }, rows.OrderBy(r => r.k is null).ThenBy(r => r.k).Select(r => r.n));

        var words = new[] { "b", "B", "a", "A" };
        var original = CultureInfo.CurrentCulture;
        try
        {
            CultureInfo.CurrentCulture = CultureInfo.InvariantCulture;
            Assert.Equal(words.OrderBy(w => w, StringComparer.CurrentCulture), words.OrderBy(w => w));
            Assert.Equal(new[] { "a", "A", "b", "B" }, words.OrderBy(w => w, StringComparer.InvariantCulture));
        }
        finally
        {
            CultureInfo.CurrentCulture = original;
        }
        Assert.Equal(new[] { "A", "B", "a", "b" }, words.OrderBy(w => w, StringComparer.Ordinal));
    }

    [Fact(DisplayName = "double.NaN は最小として先頭に置かれる")]
    public void NaNIsSmallest()
    {
        Assert.Equal(new[] { double.NaN, 1.0, 2.0 }, new[] { 2.0, double.NaN, 1.0 }.OrderBy(x => x));
    }

    [Fact(DisplayName = "空のシーケンスは空を返す")]
    public void EmptyReturnsEmpty()
    {
        Assert.Empty(Array.Empty<int>().OrderBy(x => x));
    }

    [Fact(DisplayName = "引数が null なら呼び出し時に ArgumentNullException。比較できないキー同士を比べた時点で InvalidOperationException")]
    public void ExceptionTiming()
    {
        IEnumerable<int> source = null!;
        Assert.Throws<ArgumentNullException>(() => source.OrderBy(x => x));
        Assert.Throws<ArgumentNullException>(() => new[] { 1 }.OrderBy((Func<int, int>)null!));

        var deferred = new[] { new NotComparable(), new NotComparable() }.OrderBy(x => x);
        var ex = Assert.Throws<InvalidOperationException>(() => deferred.ToList());
        Assert.IsType<ArgumentException>(ex.InnerException);

        // 要素が 1 つだけ、または null との比較だけなら投げない
        Assert.Single(new[] { new NotComparable() }.OrderBy(x => x).ToList());
        var withNull = new NotComparable?[] { new NotComparable(), null }.OrderBy(x => x).ToList();
        Assert.Null(withNull[0]);
    }
}
