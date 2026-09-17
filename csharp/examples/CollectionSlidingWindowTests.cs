// カード collection-sliding-window の Contract を検証するテスト
using MoreLinq;

public class CollectionSlidingWindowTests
{
    private static IEnumerable<int> Counting(List<int> log, int count)
    {
        for (var i = 0; i < count; i++)
        {
            log.Add(i);
            yield return i;
        }
    }

    [Fact(DisplayName = "開始位置を 1 つずつずらした窓を順序を保ったまま返す")]
    public void SlidesByOneInOrder()
    {
        var windows = new[] { 1, 2, 3, 4, 5 }.Window(3).ToList();

        Assert.Equal(new[] { new[] { 1, 2, 3 }, new[] { 2, 3, 4 }, new[] { 3, 4, 5 } }, windows);
    }

    [Fact(DisplayName = "入力を変更せず、各窓は別インスタンスで要素は同じ参照。窓を書き換えても他の窓に影響しない")]
    public void WindowsAreIndependentInstances()
    {
        var a = new object();
        var b = new object();
        var c = new object();
        var input = new[] { a, b, c };

        var windows = input.Window(2).ToList();

        Assert.Equal(new[] { a, b, c }, input);
        Assert.NotSame(windows[0], windows[1]);
        Assert.Same(b, windows[0][1]);
        Assert.Same(b, windows[1][0]);

        windows[0][1] = a;
        Assert.Same(b, windows[1][0]);
        Assert.Same(b, input[1]);
    }

    [Fact(DisplayName = "遅延評価。最初の窓を返した時点で読んでいるのは先頭の size + 1 要素")]
    public void IsLazy()
    {
        var log = new List<int>();
        var windows = Counting(log, 100).Window(3);
        Assert.Empty(log);

        using var e = windows.GetEnumerator();
        e.MoveNext();
        Assert.Equal(4, log.Count);
    }

    [Fact(DisplayName = "size に満たない末尾の窓は作られず、入力長が size 未満なら空、ちょうど size なら 1 つ")]
    public void DropsPartialWindows()
    {
        Assert.Empty(new[] { 1, 2 }.Window(3));
        Assert.Single(new[] { 1, 2, 3 }.Window(3));
        Assert.Equal(2, new[] { 1, 2, 3, 4 }.Window(3).Count());
    }

    [Fact(DisplayName = "空のシーケンスは空を返す")]
    public void EmptyReturnsEmpty()
    {
        Assert.Empty(Array.Empty<int>().Window(2));
    }

    [Fact(DisplayName = "size が 1 未満なら呼び出し時に ArgumentOutOfRangeException、source が null なら ArgumentNullException")]
    public void InvalidArgumentsThrowAtCallTime()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new[] { 1 }.Window(0));
        Assert.Throws<ArgumentOutOfRangeException>(() => new[] { 1 }.Window(-1));

        IEnumerable<int> source = null!;
        Assert.Throws<ArgumentNullException>(() => source.Window(2));
    }

    [Fact(DisplayName = "各窓の実体は固定長の配列で Add できない")]
    public void WindowIsFixedSize()
    {
        var window = new[] { 1, 2, 3 }.Window(2).First();

        Assert.IsType<int[]>(window);
        Assert.Throws<NotSupportedException>(() => window.Add(9));
    }

    [Fact(DisplayName = "WindowLeft は末尾の短い窓も返し、Pairwise は隣接 2 要素を組にする")]
    public void AlternativesBehaveAsDocumented()
    {
        var left = new[] { 1, 2, 3, 4 }.WindowLeft(3).Select(w => string.Join(",", w));
        Assert.Equal(new[] { "1,2,3", "2,3,4", "3,4", "4" }, left);

        Assert.Equal(new[] { 3, 5 }, new[] { 1, 2, 3 }.Pairwise((x, y) => x + y));
    }
}
