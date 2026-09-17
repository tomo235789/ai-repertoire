public class NumberRoundToTests
{
    [Fact(DisplayName = "指定した小数桁数で丸める")]
    public void RoundsToDigits()
    {
        Assert.Equal(1.23, Math.Round(1.2345, 2));
        Assert.Equal(1.2, Math.Round(1.2345, 1));
        Assert.Equal(1.0, Math.Round(1.2345));
    }

    [Fact(DisplayName = "既定は偶数丸めで .5 ちょうどは偶数側へ丸める")]
    public void DefaultIsToEven()
    {
        Assert.Equal(0.0, Math.Round(0.5));
        Assert.Equal(2.0, Math.Round(1.5));
        Assert.Equal(2.0, Math.Round(2.5));
        Assert.Equal(-2.0, Math.Round(-2.5));
        Assert.Equal(2m, Math.Round(2.5m));
    }

    [Fact(DisplayName = "AwayFromZero は .5 を 0 から遠い方へ丸める")]
    public void AwayFromZeroRoundsHalfAway()
    {
        Assert.Equal(3.0, Math.Round(2.5, MidpointRounding.AwayFromZero));
        Assert.Equal(-3.0, Math.Round(-2.5, MidpointRounding.AwayFromZero));
        Assert.Equal(1.5, Math.Round(1.45, 1, MidpointRounding.AwayFromZero));
        Assert.Equal(1.4, Math.Round(1.45, 1)); // 偶数丸め
    }

    [Fact(DisplayName = "ToZero などの方向指定は中間点に限らず常にその方向へ丸める")]
    public void DirectedModesAlwaysRoundThatWay()
    {
        Assert.Equal(2.0, Math.Round(2.7, MidpointRounding.ToZero));
        Assert.Equal(3.0, Math.Round(2.1, MidpointRounding.ToPositiveInfinity));
        Assert.Equal(-3.0, Math.Round(-2.1, MidpointRounding.ToNegativeInfinity));
    }

    [Fact(DisplayName = "digits は double で 0〜15、decimal で 0〜28。負の桁指定は ArgumentOutOfRangeException")]
    public void DigitsRangeIsLimited()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => Math.Round(1250.0, -1));
        Assert.Throws<ArgumentOutOfRangeException>(() => Math.Round(1.5, 16));
        Assert.Equal(1.5, Math.Round(1.5, 15));
        Assert.Throws<ArgumentOutOfRangeException>(() => Math.Round(1250m, -1));
        Assert.Throws<ArgumentOutOfRangeException>(() => Math.Round(1.5m, 29));
        Assert.Equal(1.5m, Math.Round(1.5m, 28));
    }

    [Fact(DisplayName = "double は 10 の digits 乗を掛けてから丸めるので 2 進数の表現誤差が出る")]
    public void DoubleRoundingReflectsBinaryRepresentation()
    {
        Assert.Equal(100.49999999999999, 1.005 * 100);
        Assert.Equal(1.0, Math.Round(1.005, 2));
        Assert.Equal(1.0, Math.Round(1.005, 2, MidpointRounding.AwayFromZero));
        Assert.Equal(267.5, 2.675 * 100);
        Assert.Equal(2.68, Math.Round(2.675, 2));
    }

    [Fact(DisplayName = "decimal は 10 進のまま丸めるので 1.005 を正しく扱える")]
    public void DecimalRoundsExactly()
    {
        Assert.Equal(1.00m, Math.Round(1.005m, 2));
        Assert.Equal(1.01m, Math.Round(1.005m, 2, MidpointRounding.AwayFromZero));
        Assert.Equal(2.68m, Math.Round(2.675m, 2));
    }

    [Fact(DisplayName = "返り値は入力と同じ型で、NaN と無限大はそのまま返る")]
    public void PreservesTypeAndSpecialValues()
    {
        Assert.IsType<double>(Math.Round(2.5));
        Assert.IsType<decimal>(Math.Round(2.5m));
        Assert.True(double.IsNaN(Math.Round(double.NaN, 2)));
        Assert.Equal(double.PositiveInfinity, Math.Round(double.PositiveInfinity, 2));
        Assert.Equal(double.NegativeInfinity, 1 / Math.Round(-0.4)); // -0 が返る
    }

    [Fact(DisplayName = "未定義の MidpointRounding 値は ArgumentException")]
    public void InvalidModeThrows()
    {
        Assert.Throws<ArgumentException>(() => Math.Round(2.5, (MidpointRounding)9));
    }

    [Fact(DisplayName = "MathF.Round と double.Round も同じ丸め規則で動く")]
    public void AlternativesMatch()
    {
        Assert.Equal(2f, MathF.Round(2.5f));
        Assert.Equal(3.0, double.Round(2.5, 0, MidpointRounding.AwayFromZero));
        Assert.Equal(1230.0, Math.Round(1234.0 / 10, MidpointRounding.AwayFromZero) * 10); // 10 の位で丸める
    }
}
