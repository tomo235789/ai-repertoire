using System.Globalization;
using System.Text;

public class StringTruncateTests
{
    private static string Truncate(string s, int n) => s.Length <= n ? s : s[..(n - 3)] + "...";

    [Fact(DisplayName = "上限を超えたら先頭 n-3 文字と省略記号でちょうど n 文字にする")]
    public void TruncatesToLengthIncludingEllipsis()
    {
        var text = "The quick brown fox jumps over the lazy dog";
        var result = Truncate(text, 20);
        Assert.Equal("The quick brown f...", result);
        Assert.Equal(20, result.Length);
    }

    [Fact(DisplayName = "上限以下なら同じインスタンスをそのまま返す")]
    public void ReturnsSameInstanceWhenShortEnough()
    {
        var s = "abcde";
        Assert.Same(s, Truncate(s, 5));
        Assert.Same(s, Truncate(s, 10));
        Assert.Equal("", Truncate("", 0));
    }

    [Fact(DisplayName = "切り詰めが必要で n が 3 未満なら ArgumentOutOfRangeException、n == 3 なら省略記号だけ")]
    public void SmallLimits()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => Truncate("abcde", 2));
        Assert.Equal("...", Truncate("abcde", 3));
    }

    [Fact(DisplayName = "UTF-16 コード単位で数えるのでサロゲートペアの途中で切れる")]
    public void MayCutSurrogatePair()
    {
        var s = "ab😀cde"; // Length は 7
        Assert.Equal(7, s.Length);
        var result = Truncate(s, 6);
        Assert.Equal(6, result.Length);
        Assert.True(char.IsHighSurrogate(result[2]));
        Assert.False(char.IsLowSurrogate(result[3]));
        Assert.Equal(new byte[] { 0x61, 0x62, 0xEF, 0xBF, 0xBD, 0x2E, 0x2E, 0x2E }, Encoding.UTF8.GetBytes(result));
    }

    [Fact(DisplayName = "null を渡すと NullReferenceException")]
    public void NullThrows()
    {
        Assert.Throws<NullReferenceException>(() => Truncate(null!, 5));
    }

    [Fact(DisplayName = "入力を変更せず新しい文字列を返す")]
    public void DoesNotMutateInput()
    {
        var s = "abcdefgh";
        var result = Truncate(s, 6);
        Assert.Equal("abcdefgh", s);
        Assert.NotSame(s, result);
    }

    [Fact(DisplayName = "1 文字の省略記号、Concat、StringInfo による別解")]
    public void Alternatives()
    {
        Assert.Equal("abc…", "abcdef".Length <= 4 ? "abcdef" : "abcdef"[..3] + "…");
        Assert.Equal("abc...", string.Concat("abcdef".AsSpan(0, 3), "..."));
        Assert.Equal("ab😀...", new StringInfo("ab😀cde").SubstringByTextElements(0, 3) + "...");
        Assert.Equal("ab😀...", string.Concat("ab😀cde".EnumerateRunes().Take(3).Select(r => r.ToString())) + "...");
    }

    [Fact(DisplayName = "範囲演算子は n > Length で ArgumentOutOfRangeException なので Length の判定が先に要る")]
    public void RangeOperatorThrowsBeyondLength()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => "abc"[..5]);
        Assert.Throws<ArgumentOutOfRangeException>(() => "abc".Substring(0, 5));
    }
}
