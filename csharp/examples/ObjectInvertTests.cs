// カード object-invert の Contract を検証するテスト
public class ObjectInvertTests
{
    [Fact(DisplayName = "キーと値を入れ替えた新しい Dictionary を返す。型は文字列化しない")]
    public void SwapsKeysAndValues()
    {
        var codeToName = new Dictionary<int, string> { [1] = "red", [2] = "blue" };

        var nameToCode = codeToName.ToDictionary(kv => kv.Value, kv => kv.Key);

        Assert.Equal(new Dictionary<string, int> { ["red"] = 1, ["blue"] = 2 }, nameToCode);
        Assert.IsType<int>(nameToCode["red"]);
    }

    [Fact(DisplayName = "入力辞書を変更せず、返り値は新しい Dictionary")]
    public void DoesNotMutateInput()
    {
        var d = new Dictionary<string, int> { ["a"] = 1 };

        var inverted = d.ToDictionary(kv => kv.Value, kv => kv.Key);

        Assert.Equal(new Dictionary<string, int> { ["a"] = 1 }, d);
        Assert.Equal("a", inverted[1]);
    }

    [Fact(DisplayName = "即時評価で元の辞書の列挙順で追加される")]
    public void IsEagerAndKeepsOrder()
    {
        var d = new Dictionary<string, int> { ["c"] = 3, ["a"] = 1, ["b"] = 2 };

        var inverted = d.ToDictionary(kv => kv.Value, kv => kv.Key);

        Assert.Equal(new[] { 3, 1, 2 }, inverted.Keys);
    }

    [Fact(DisplayName = "値が重複していると ArgumentException")]
    public void DuplicateValuesThrow()
    {
        var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 1 };

        Assert.Throws<ArgumentException>(() => d.ToDictionary(kv => kv.Value, kv => kv.Key));
    }

    [Fact(DisplayName = "値に null があると ArgumentNullException")]
    public void NullValueThrows()
    {
        var d = new Dictionary<string, string?> { ["a"] = null };

        Assert.Throws<ArgumentNullException>(() => d.ToDictionary(kv => kv.Value!, kv => kv.Key));
    }

    [Fact(DisplayName = "キーの比較は既定で Equals。比較器を渡すと大文字小文字を無視できる（重複すれば ArgumentException）")]
    public void ComparerCanBeGiven()
    {
        var d = new Dictionary<int, string> { [1] = "a", [2] = "A" };

        Assert.Equal(2, d.ToDictionary(kv => kv.Value, kv => kv.Key).Count);
        Assert.Throws<ArgumentException>(() => d.ToDictionary(kv => kv.Value, kv => kv.Key, StringComparer.OrdinalIgnoreCase));
    }

    [Fact(DisplayName = "空の辞書は空の Dictionary を返す")]
    public void EmptyReturnsEmpty()
    {
        var d = new Dictionary<string, int>();

        Assert.Empty(d.ToDictionary(kv => kv.Value, kv => kv.Key));
    }

    [Fact(DisplayName = "source が null なら呼び出し時に ArgumentNullException")]
    public void NullSourceThrows()
    {
        Dictionary<string, int> d = null!;

        Assert.Throws<ArgumentNullException>(() => d.ToDictionary(kv => kv.Value, kv => kv.Key));
    }

    [Fact(DisplayName = "重複する値をまとめるなら ToLookup、最後を残すなら上書きループ")]
    public void AlternativesForDuplicates()
    {
        var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 1, ["c"] = 2 };

        var lookup = d.ToLookup(kv => kv.Value, kv => kv.Key);
        Assert.Equal(new[] { "a", "b" }, lookup[1]);

        var lastWins = new Dictionary<int, string>();
        foreach (var kv in d) lastWins[kv.Value] = kv.Key;
        Assert.Equal("b", lastWins[1]);
    }
}
