public class NumberSumByTests
{
    private sealed record Item(string Name, int Qty);

    [Fact(DisplayName = "各要素から取り出した数値を合計する")]
    public void SumsSelectedValues()
    {
        var items = new[] { new Item("a", 2), new Item("b", 3) };
        Assert.Equal(5, items.Sum(item => item.Qty));
    }

    [Fact(DisplayName = "入力を変更しない")]
    public void DoesNotMutateInput()
    {
        var items = new List<Item> { new("a", 2), new("b", 3) };
        items.Sum(item => item.Qty);
        Assert.Equal([new Item("a", 2), new Item("b", 3)], items);
    }

    [Fact(DisplayName = "selector は各要素につき 1 回、先頭から順に呼ばれる（即時評価）")]
    public void SelectorIsCalledOncePerElementInOrder()
    {
        var seen = new List<int>();
        new[] { 10, 20, 30 }.Sum(x => { seen.Add(x); return x; });
        Assert.Equal([10, 20, 30], seen);
    }

    [Fact(DisplayName = "空なら 0 を返す")]
    public void EmptyReturnsZero()
    {
        Assert.Equal(0, Array.Empty<Item>().Sum(item => item.Qty));
        Assert.Equal(0.0, Array.Empty<Item>().Sum(item => (double)item.Qty));
    }

    [Fact(DisplayName = "返り値の型は selector の返り値の型になる")]
    public void ReturnTypeFollowsSelector()
    {
        Assert.IsType<long>(new[] { 1 }.Sum(x => (long)x));
        Assert.IsType<float>(new[] { 1 }.Sum(x => (float)x));
        Assert.IsType<decimal>(new[] { 1 }.Sum(x => (decimal)x));
    }

    [Fact(DisplayName = "int / long / decimal の桁あふれは OverflowException")]
    public void IntegerOverflowThrows()
    {
        Assert.Throws<OverflowException>(() => new[] { int.MaxValue, 1 }.Sum(x => x));
        Assert.Throws<OverflowException>(() => new[] { long.MaxValue, 1 }.Sum(x => x));
        Assert.Throws<OverflowException>(() => new[] { decimal.MaxValue, 1m }.Sum(x => x));
    }

    [Fact(DisplayName = "double の桁あふれは例外にならず無限大になる")]
    public void DoubleOverflowBecomesInfinity()
    {
        Assert.Equal(double.PositiveInfinity, new[] { double.MaxValue, double.MaxValue }.Sum(x => x));
    }

    [Fact(DisplayName = "Nullable の null は無視され、全部 null でも 0")]
    public void NullsAreIgnored()
    {
        Assert.Equal(3, new int?[] { 1, null, 2 }.Sum(x => x));
        Assert.Equal(0, new int?[] { null, null }.Sum(x => x));
    }

    [Fact(DisplayName = "NaN があれば NaN、浮動小数点の誤差は補正されない")]
    public void FloatingPointBehaviour()
    {
        Assert.True(double.IsNaN(new[] { 1.0, double.NaN }.Sum(x => x)));
        Assert.Equal(0.9999999999999999, Enumerable.Repeat(0.1, 10).Sum(x => x));
    }

    [Fact(DisplayName = "source や selector が null なら ArgumentNullException、selector の例外はそのまま伝播する")]
    public void NullArgumentsAndCallbackExceptions()
    {
        Assert.Throws<ArgumentNullException>(() => ((int[])null!).Sum(x => x));
        Assert.Throws<ArgumentNullException>(() => new[] { 1 }.Sum((Func<int, int>)null!));
        Assert.Throws<InvalidOperationException>(() => new[] { 1 }.Sum(x => throw new InvalidOperationException("boom")));
    }

    [Fact(DisplayName = "selector で long に広げれば int の桁あふれを避けられる")]
    public void WideningInSelectorAvoidsOverflow()
    {
        Assert.Equal(int.MaxValue + 1L, new[] { int.MaxValue, 1 }.Sum(x => (long)x));
    }
}
