public class StringPadTests
{
    [Fact(DisplayName = "左または右に文字を詰めて指定の長さにする")]
    public void PadsToWidth()
    {
        Assert.Equal("   abc", "abc".PadLeft(6));
        Assert.Equal("abc***", "abc".PadRight(6, '*'));
        Assert.Equal("***abc", "abc".PadLeft(6, '*'));
        Assert.Equal("005", 5.ToString().PadLeft(3, '0'));
    }

    [Fact(DisplayName = "元の文字列は変わらず、新しい文字列を返す")]
    public void DoesNotMutate()
    {
        var s = "abc";
        var padded = s.PadLeft(6);
        Assert.Equal("abc", s);
        Assert.NotSame(s, padded);
    }

    [Fact(DisplayName = "totalWidth が Length 以下なら元の文字列をそのまま返し、切り詰めない")]
    public void ShortWidthReturnsOriginal()
    {
        Assert.Equal("abc", "abc".PadLeft(2));
        Assert.Equal("abc", "abc".PadLeft(0));
        Assert.Same("abc", "abc".PadLeft(3));
    }

    [Fact(DisplayName = "totalWidth が負なら ArgumentOutOfRangeException")]
    public void NegativeWidthThrows()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => "abc".PadLeft(-1));
        Assert.Throws<ArgumentOutOfRangeException>(() => "abc".PadRight(-1));
    }

    [Fact(DisplayName = "長さは UTF-16 コード単位で数える")]
    public void CountsUtf16CodeUnits()
    {
        Assert.Equal(2, "😀".Length);
        Assert.Equal("*😀", "😀".PadLeft(3, '*'));
        Assert.Equal("*é", "é".PadLeft(3, '*'));
        Assert.Equal("**あ", "あ".PadLeft(3, '*'));
    }

    [Fact(DisplayName = "空文字は paddingChar だけで埋まる")]
    public void EmptyStringIsAllPadding()
    {
        Assert.Equal("   ", "".PadLeft(3));
        Assert.Equal("***", "".PadRight(3, '*'));
    }

    [Fact(DisplayName = "中央寄せのイディオムは余りを右側に寄せる（es-toolkit の pad と同じ）")]
    public void CenterIdiomMatchesEsToolkit()
    {
        static string Center(string s, int width) => s.PadLeft((width + s.Length) / 2).PadRight(width);
        Assert.Equal("  abc   ", Center("abc", 8));
        Assert.Equal("abc ", Center("abc", 4));
        Assert.Equal(" ab  ", Center("ab", 5));
        Assert.Equal("abc", Center("abc", 2));
    }

    [Fact(DisplayName = "補間文字列の配置指定と D 書式でも同じ桁揃えができる")]
    public void AlternativesAlign()
    {
        Assert.Equal("   abc", $"{"abc",6}");
        Assert.Equal("abc   ", $"{"abc",-6}");
        Assert.Equal("005", 5.ToString("D3"));
        Assert.Equal("-005", (-5).ToString("D3"));
        Assert.Equal("00-5", (-5).ToString().PadLeft(4, '0'));
    }
}
