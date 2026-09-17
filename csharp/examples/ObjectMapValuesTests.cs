// カード object-map-values の Contract を検証するテスト
public class ObjectMapValuesTests
{
    [Fact(DisplayName = "キーはそのままに各値だけを変換した新しい Dictionary を返す")]
    public void MapsValuesKeepingKeys()
    {
        var scores = new Dictionary<string, int[]> { ["alice"] = new[] { 80, 90 }, ["bob"] = new[] { 70 } };

        var counts = scores.ToDictionary(kv => kv.Key, kv => kv.Value.Length);

        Assert.Equal(new Dictionary<string, int> { ["alice"] = 2, ["bob"] = 1 }, counts);
    }

    [Fact(DisplayName = "元の辞書の列挙順で追加される")]
    public void KeepsOriginalOrder()
    {
        var d = new Dictionary<string, int> { ["c"] = 3, ["a"] = 1, ["b"] = 2 };

        var mapped = d.ToDictionary(kv => kv.Key, kv => kv.Value * 10);

        Assert.Equal(new[] { "c", "a", "b" }, mapped.Keys);
    }

    [Fact(DisplayName = "入力辞書を変更せず、返り値は新しい Dictionary。入力の値を返せば同じ参照")]
    public void DoesNotMutateInputAndReturnsNewDictionary()
    {
        var value = new object();
        var d = new Dictionary<string, object> { ["a"] = value };

        var mapped = d.ToDictionary(kv => kv.Key, kv => kv.Value);

        Assert.NotSame(d, mapped);
        Assert.Same(value, mapped["a"]);
        Assert.Same(value, d["a"]);
    }

    [Fact(DisplayName = "即時評価。elementSelector は列挙順に各要素につきちょうど 1 回呼ばれる")]
    public void IsEagerAndCallsSelectorOncePerElement()
    {
        var called = new List<string>();
        var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };

        d.ToDictionary(kv => kv.Key, kv =>
        {
            called.Add(kv.Key);
            return kv.Value;
        });

        Assert.Equal(new[] { "a", "b" }, called);
    }

    [Fact(DisplayName = "elementSelector が途中で例外を投げるとそこで止まり、以降の要素には呼ばれない")]
    public void StopsAtFirstSelectorException()
    {
        var called = new List<string>();
        var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2, ["c"] = 3 };

        Assert.Throws<InvalidOperationException>(() => d.ToDictionary(kv => kv.Key, int (kv) =>
        {
            called.Add(kv.Key);
            return kv.Key == "b" ? throw new InvalidOperationException("boom") : kv.Value;
        }));

        Assert.Equal(new[] { "a", "b" }, called);
    }

    [Fact(DisplayName = "元の辞書の比較器は引き継がれない。第 4 引数に渡せば引き継げる")]
    public void ComparerIsNotInheritedUnlessPassed()
    {
        var d = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase) { ["ID"] = 1 };

        var mapped = d.ToDictionary(kv => kv.Key, kv => kv.Value * 2);
        Assert.False(mapped.ContainsKey("id"));

        var withComparer = d.ToDictionary(kv => kv.Key, kv => kv.Value * 2, d.Comparer);
        Assert.Equal(2, withComparer["id"]);
    }

    [Fact(DisplayName = "元より緩い比較器を渡すと同一視されるキーで ArgumentException")]
    public void LooserComparerCausesDuplicateKeys()
    {
        var d = new Dictionary<string, int> { ["id"] = 1, ["ID"] = 2 };

        Assert.Throws<ArgumentException>(() => d.ToDictionary(kv => kv.Key, kv => kv.Value, StringComparer.OrdinalIgnoreCase));
        Assert.Equal(2, d.ToDictionary(kv => kv.Key, kv => kv.Value, d.Comparer).Count);
    }

    [Fact(DisplayName = "空の辞書は空の Dictionary を返す")]
    public void EmptyReturnsEmpty()
    {
        var d = new Dictionary<string, int>();

        Assert.Empty(d.ToDictionary(kv => kv.Key, kv => kv.Value + 1));
    }

    [Fact(DisplayName = "source が null なら ArgumentNullException。elementSelector の例外はそのまま伝播する")]
    public void NullSourceAndSelectorExceptions()
    {
        Dictionary<string, int> nul = null!;
        Assert.Throws<ArgumentNullException>(() => nul.ToDictionary(kv => kv.Key, kv => kv.Value));

        var d = new Dictionary<string, int> { ["a"] = 1 };
        Assert.Throws<InvalidOperationException>(
            () => d.ToDictionary(kv => kv.Key, int (kv) => throw new InvalidOperationException("boom")));
    }

    [Fact(DisplayName = "elementSelector の中で入力辞書に追加すると InvalidOperationException")]
    public void ModifyingInputDuringMappingThrows()
    {
        var d = new Dictionary<string, int> { ["a"] = 1 };

        Assert.Throws<InvalidOperationException>(() => d.ToDictionary(kv => kv.Key, kv =>
        {
            d["z"] = 9;
            return kv.Value;
        }));
    }
}
