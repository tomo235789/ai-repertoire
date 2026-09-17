// カード object-pick の Contract を検証するテスト
public class ObjectPickTests
{
    private static Dictionary<string, TValue> Pick<TValue>(Dictionary<string, TValue> d, IEnumerable<string> keys)
    {
        return keys.Where(d.ContainsKey).ToDictionary(k => k, k => d[k]);
    }

    [Fact(DisplayName = "指定したキーだけを持つ新しい Dictionary を返す")]
    public void ReturnsOnlyRequestedKeys()
    {
        var user = new Dictionary<string, object> { ["id"] = 1, ["name"] = "a", ["password"] = "x" };

        var picked = Pick(user, new[] { "id", "name" });

        Assert.Equal(new Dictionary<string, object> { ["id"] = 1, ["name"] = "a" }, picked);
    }

    [Fact(DisplayName = "入力辞書を変更せず、値は同じ参照")]
    public void DoesNotMutateInputAndKeepsReferences()
    {
        var value = new object();
        var d = new Dictionary<string, object> { ["a"] = value, ["b"] = new object() };

        var picked = Pick(d, new[] { "a" });

        Assert.Equal(2, d.Count);
        Assert.NotSame(d, picked);
        Assert.Same(value, picked["a"]);
    }

    [Fact(DisplayName = "存在しないキーは無視され、null の値はそのまま含まれる")]
    public void IgnoresMissingKeysAndKeepsNullValues()
    {
        var d = new Dictionary<string, string?> { ["a"] = null, ["b"] = "x" };

        var picked = Pick(d, new[] { "a", "missing" });

        Assert.Single(picked);
        Assert.True(picked.ContainsKey("a"));
        Assert.Null(picked["a"]);
        Assert.False(picked.ContainsKey("missing"));
    }

    [Fact(DisplayName = "keys の並び順で追加される")]
    public void AddsInKeysOrder()
    {
        var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2, ["c"] = 3 };

        var picked = Pick(d, new[] { "c", "a" });

        Assert.Equal(new[] { "c", "a" }, picked.Keys);
    }

    [Fact(DisplayName = "keys に重複があると ArgumentException。Distinct を挟めば通る")]
    public void DuplicateKeysThrow()
    {
        var d = new Dictionary<string, int> { ["a"] = 1 };

        Assert.Throws<ArgumentException>(() => Pick(d, new[] { "a", "a" }));
        Assert.Single(Pick(d, new[] { "a", "a" }.Distinct()));
    }

    [Fact(DisplayName = "元の辞書の比較器は引き継がれない。渡せば引き継げる")]
    public void ComparerIsNotInheritedUnlessPassed()
    {
        var d = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase) { ["ID"] = 1 };
        var keys = new[] { "id" };

        var picked = Pick(d, keys);
        Assert.True(picked.ContainsKey("id"));
        Assert.False(picked.ContainsKey("ID"));

        var withComparer = keys.Where(d.ContainsKey).ToDictionary(k => k, k => d[k], d.Comparer);
        Assert.True(withComparer.ContainsKey("ID"));
    }

    [Fact(DisplayName = "keys が空なら空の Dictionary を返す")]
    public void EmptyKeysReturnsEmpty()
    {
        var d = new Dictionary<string, int> { ["a"] = 1 };

        Assert.Empty(Pick(d, Array.Empty<string>()));
    }

    [Fact(DisplayName = "keys が null なら ArgumentNullException。keys の要素が null なら ContainsKey が ArgumentNullException")]
    public void NullKeysThrow()
    {
        var d = new Dictionary<string, int> { ["a"] = 1 };

        Assert.Throws<ArgumentNullException>(() => Pick(d, null!));
        Assert.Throws<ArgumentNullException>(() => Pick(d, new string[] { null! }));
    }

    [Fact(DisplayName = "存在しないキーで失敗させたいなら Where を外すと KeyNotFoundException")]
    public void WithoutWhereMissingKeyThrows()
    {
        var d = new Dictionary<string, int> { ["a"] = 1 };

        Assert.Throws<KeyNotFoundException>(() => new[] { "missing" }.ToDictionary(k => k, k => d[k]));
    }
}
