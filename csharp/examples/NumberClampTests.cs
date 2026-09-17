public class NumberClampTests
{
    [Fact(DisplayName = "範囲を超えた値は境界値に置き換えられ、範囲内の値はそのまま返る")]
    public void ClampsToRange()
    {
        Assert.Equal(100, Math.Clamp(120, 0, 100));
        Assert.Equal(0, Math.Clamp(-5, 0, 100));
        Assert.Equal(42, Math.Clamp(42, 0, 100));
    }

    [Fact(DisplayName = "境界値は範囲に含まれる")]
    public void BoundariesAreInclusive()
    {
        Assert.Equal(0, Math.Clamp(0, 0, 100));
        Assert.Equal(100, Math.Clamp(100, 0, 100));
    }

    [Fact(DisplayName = "min > max なら value に関係なく ArgumentException を投げる")]
    public void ThrowsWhenMinGreaterThanMax()
    {
        Assert.Throws<ArgumentException>(() => Math.Clamp(5, 10, 1));
        Assert.Throws<ArgumentException>(() => Math.Clamp(5.0, 10.0, 1.0));
        Assert.Throws<ArgumentException>(() => Math.Clamp(50, 10, 1)); // 範囲外の value でも同じ
    }

    [Fact(DisplayName = "value が NaN なら NaN を返す")]
    public void NaNValueReturnsNaN()
    {
        Assert.True(double.IsNaN(Math.Clamp(double.NaN, 0.0, 10.0)));
    }

    [Fact(DisplayName = "min や max が NaN のときはその境界だけが効かない")]
    public void NaNBoundIsIgnored()
    {
        Assert.Equal(-1.0, Math.Clamp(-1.0, double.NaN, 10.0)); // 下限が効かない
        Assert.Equal(10.0, Math.Clamp(15.0, double.NaN, 10.0)); // 上限は効く
        Assert.Equal(15.0, Math.Clamp(15.0, 0.0, double.NaN));  // 上限が効かない
        Assert.Equal(0.0, Math.Clamp(-1.0, 0.0, double.NaN));   // 下限は効く
    }

    [Fact(DisplayName = "型変換はせず、int と double を混ぜると double の多重定義が選ばれる")]
    public void PreservesTypeAndPicksWidestOverload()
    {
        Assert.Equal(1.0, Math.Clamp(1.5, 0.0, 1.0));
        Assert.Equal(1m, Math.Clamp(1.5m, 0m, 1m));
        Assert.Equal((byte)100, Math.Clamp((byte)200, (byte)0, (byte)100));
        var mixed = Math.Clamp(5, 1, 3.5);
        Assert.IsType<double>(mixed);
        Assert.Equal(3.5, mixed);
    }

    [Fact(DisplayName = "純粋関数で引数を変更しない")]
    public void DoesNotMutateArguments()
    {
        var value = 120;
        var min = 0;
        var max = 100;
        Math.Clamp(value, min, max);
        Assert.Equal((120, 0, 100), (value, min, max));
    }

    [Fact(DisplayName = ".NET 7 以降のジェネリック数学 T.Clamp でも同じ結果になる")]
    public void GenericMathClampMatches()
    {
        Assert.Equal(100, int.Clamp(120, 0, 100));
        Assert.Equal(0.0, double.Clamp(-0.5, 0.0, 1.0));
        Assert.Throws<ArgumentException>(() => int.Clamp(5, 10, 1));
    }

    [Fact(DisplayName = "Math.Min / Math.Max の組み合わせは min > max で例外を投げず max を返す")]
    public void MinMaxIdiomDiffersWhenReversed()
    {
        Assert.Equal(1, Math.Min(Math.Max(5, 10), 1));
    }
}
