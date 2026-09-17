// カード collection-chunk の Contract を検証するテスト
public class CollectionChunkTests
{
    // 読み取った要素を log に記録する遅延シーケンス
    private static IEnumerable<int> Counting(List<int> log, int count)
    {
        for (var i = 0; i < count; i++)
        {
            log.Add(i);
            yield return i;
        }
    }

    [Fact(DisplayName = "順序を保ったまま size ごとに分割し、最後は短くなる")]
    public void SplitsInOrderAndLastChunkIsShorter()
    {
        var chunks = new[] { 1, 2, 3, 4, 5 }.Chunk(2).ToList();

        Assert.Equal(new[] { new[] { 1, 2 }, new[] { 3, 4 }, new[] { 5 } }, chunks);
    }

    [Fact(DisplayName = "入力を変更せず、各チャンクは新しい配列で要素は同じ参照")]
    public void DoesNotMutateInputAndChunksAreNewArrays()
    {
        var a = new object();
        var b = new object();
        var input = new[] { a, b };

        var chunks = input.Chunk(1).ToList();

        Assert.Equal(new[] { a, b }, input);
        Assert.NotSame(input, chunks[0]);
        Assert.NotSame(chunks[0], chunks[1]);
        Assert.Same(a, chunks[0][0]);
        Assert.Same(b, chunks[1][0]);
    }

    [Fact(DisplayName = "遅延評価。チャンク 1 つ分ずつ読み進め、列挙のたびに入力を読み直す")]
    public void IsLazyAndReenumeratesInput()
    {
        var log = new List<int>();
        var chunks = Counting(log, 10).Chunk(3);
        Assert.Empty(log);

        using var e = chunks.GetEnumerator();
        e.MoveNext();
        Assert.Equal(new[] { 0, 1, 2 }, log);

        log.Clear();
        chunks.ToList();
        chunks.ToList();
        Assert.Equal(20, log.Count);
    }

    [Fact(DisplayName = "空のシーケンスは空を返す")]
    public void EmptyReturnsEmpty()
    {
        Assert.Empty(Array.Empty<int>().Chunk(3));
    }

    [Fact(DisplayName = "size が 1 未満なら列挙を待たず呼び出し時に ArgumentOutOfRangeException")]
    public void SizeLessThanOneThrowsAtCallTime()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => new[] { 1, 2 }.Chunk(0));
        Assert.Throws<ArgumentOutOfRangeException>(() => new[] { 1, 2 }.Chunk(-1));
    }

    [Fact(DisplayName = "source が null なら呼び出し時に ArgumentNullException")]
    public void NullSourceThrowsAtCallTime()
    {
        IEnumerable<int> source = null!;
        Assert.Throws<ArgumentNullException>(() => source.Chunk(2));
    }

    [Fact(DisplayName = "文字列は char 単位で分割され、サロゲートペアが分断される")]
    public void StringIsChunkedByChar()
    {
        Assert.Equal(3, "𠮷a".Chunk(1).Count());
    }
}
