public class NumberMeanTests
{
    [Fact(DisplayName = "算術平均を返し、int でも double になる")]
    public void ReturnsArithmeticMeanAsDouble()
    {
        Assert.Equal(3.0, new[] { 1, 2, 3, 4, 5 }.Average());
        var mean = new[] { 1, 2 }.Average();
        Assert.IsType<double>(mean);
        Assert.Equal(1.5, mean);
        Assert.IsType<double>(new[] { 1L, 2L }.Average());
        Assert.IsType<float>(new[] { 1f, 2f }.Average());
        Assert.IsType<decimal>(new[] { 1m, 2m }.Average());
    }

    [Fact(DisplayName = "空のシーケンスは InvalidOperationException を投げる")]
    public void EmptyThrows()
    {
        Assert.Throws<InvalidOperationException>(() => Array.Empty<int>().Average());
        Assert.Throws<InvalidOperationException>(() => Array.Empty<double>().Average());
    }

    [Fact(DisplayName = "Nullable は null を無視して残りの件数で割り、空や全部 null なら null")]
    public void NullableIgnoresNulls()
    {
        Assert.Equal(1.5, new int?[] { 1, null, 2 }.Average());
        Assert.Null(Array.Empty<int?>().Average());
        Assert.Null(new int?[] { null, null }.Average());
    }

    [Fact(DisplayName = "入力を変更せず、1 回だけ走査する")]
    public void DoesNotMutateAndEnumeratesOnce()
    {
        var xs = new List<int> { 3, 1, 2 };
        var reads = 0;
        IEnumerable<int> Source() { foreach (var x in xs) { reads++; yield return x; } }
        Source().Average();
        Assert.Equal([3, 1, 2], xs);
        Assert.Equal(3, reads);
    }

    [Fact(DisplayName = "int は long で合計するので桁あふれせず、long の合計は OverflowException")]
    public void OverflowBehaviour()
    {
        Assert.Equal(int.MaxValue, new[] { int.MaxValue, int.MaxValue }.Average());
        Assert.Throws<OverflowException>(() => new[] { long.MaxValue, long.MaxValue }.Average());
    }

    [Fact(DisplayName = "NaN があれば NaN、+∞ と -∞ を両方含むと NaN")]
    public void NaNAndInfinity()
    {
        Assert.True(double.IsNaN(new[] { 1.0, double.NaN }.Average()));
        Assert.True(double.IsNaN(new[] { double.PositiveInfinity, double.NegativeInfinity }.Average()));
    }

    [Fact(DisplayName = "浮動小数点の誤差はそのまま")]
    public void FloatingPointError()
    {
        Assert.Equal(0.20000000000000004, new[] { 0.1, 0.2, 0.3 }.Average());
    }

    [Fact(DisplayName = "source が null なら ArgumentNullException")]
    public void NullSourceThrows()
    {
        Assert.Throws<ArgumentNullException>(() => ((int[])null!).Average());
    }

    [Fact(DisplayName = "selector 付きの多重定義と、空を既定値にするイディオム")]
    public void SelectorAndDefaultIfEmpty()
    {
        Assert.Equal(2.0, new[] { "a", "bbb" }.Average(s => s.Length));
        Assert.Equal(0.0, Array.Empty<int>().DefaultIfEmpty().Average());
        Assert.Equal(1.0, new int?[] { 1, null, 2 }.Average(x => x ?? 0));
    }
}
