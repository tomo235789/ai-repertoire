// カード object-omit の Contract を検証するテスト
public class ObjectOmitTests
{
    private static Dictionary<string, TValue> Omit<TValue>(Dictionary<string, TValue> d, HashSet<string> excluded)
    {
        return d.Where(kv => !excluded.Contains(kv.Key)).ToDictionary();
    }

    [Fact(DisplayName = "指定したキーを除いた新しい Dictionary を返す")]
    public void RemovesExcludedKeys()
    {
        var user = new Dictionary<string, object> { ["id"] = 1, ["name"] = "a", ["password"] = "x" };

        var rest = Omit(user, new HashSet<string> { "password" });

        Assert.Equal(new Dictionary<string, object> { ["id"] = 1, ["name"] = "a" }, rest);
    }

    [Fact(DisplayName = "入力辞書を変更せず、値は同じ参照")]
    public void DoesNotMutateInputAndKeepsReferences()
    {
        var value = new object();
        var d = new Dictionary<string, object> { ["a"] = value, ["b"] = new object() };

        var rest = Omit(d, new HashSet<string> { "b" });

        Assert.Equal(2, d.Count);
        Assert.NotSame(d, rest);
        Assert.Same(value, rest["a"]);
    }

    [Fact(DisplayName = "残ったキーは元の辞書の列挙順で追加される")]
    public void KeepsOriginalOrder()
    {
        var d = new Dictionary<string, int> { ["c"] = 3, ["a"] = 1, ["b"] = 2 };

        var rest = Omit(d, new HashSet<string> { "a" });

        Assert.Equal(new[] { "c", "b" }, rest.Keys);
    }

    [Fact(DisplayName = "存在しないキーを excluded に入れても無視される")]
    public void IgnoresMissingKeys()
    {
        var d = new Dictionary<string, int> { ["a"] = 1 };

        Assert.Equal(d, Omit(d, new HashSet<string> { "missing" }));
    }

    [Fact(DisplayName = "すべて除くと空。excluded が空なら同じ内容の別インスタンス")]
    public void AllOrNothing()
    {
        var d = new Dictionary<string, int> { ["a"] = 1, ["b"] = 2 };

        Assert.Empty(Omit(d, new HashSet<string> { "a", "b" }));

        var copy = Omit(d, new HashSet<string>());
        Assert.Equal(d, copy);
        Assert.NotSame(d, copy);
    }

    [Fact(DisplayName = "元の辞書の比較器は引き継がれない。渡せば引き継げる")]
    public void ComparerIsNotInheritedUnlessPassed()
    {
        var d = new Dictionary<string, int>(StringComparer.OrdinalIgnoreCase) { ["ID"] = 1 };

        var rest = Omit(d, new HashSet<string>());
        Assert.False(rest.ContainsKey("id"));

        var withComparer = d.Where(kv => true).ToDictionary(kv => kv.Key, kv => kv.Value, d.Comparer);
        Assert.True(withComparer.ContainsKey("id"));
    }

    [Fact(DisplayName = "excluded の比較器で大文字小文字を無視して除ける")]
    public void ExcludedComparerControlsMatching()
    {
        var d = new Dictionary<string, int> { ["Password"] = 1, ["id"] = 2 };

        var rest = Omit(d, new HashSet<string>(StringComparer.OrdinalIgnoreCase) { "password" });

        Assert.Equal(new[] { "id" }, rest.Keys);
    }

    [Fact(DisplayName = "元より緩い比較器を ToDictionary に渡すと同一視されるキーで ArgumentException。d.Comparer なら起きない")]
    public void LooserComparerCausesDuplicateKeys()
    {
        var d = new Dictionary<string, int> { ["id"] = 1, ["ID"] = 2 };

        Assert.Throws<ArgumentException>(
            () => d.Where(kv => true).ToDictionary(kv => kv.Key, kv => kv.Value, StringComparer.OrdinalIgnoreCase));
        Assert.Equal(2, d.Where(kv => true).ToDictionary(kv => kv.Key, kv => kv.Value, d.Comparer).Count);
    }

    [Fact(DisplayName = "d が null なら Where の呼び出し時に ArgumentNullException")]
    public void NullDictionaryThrows()
    {
        Dictionary<string, int> d = null!;

        Assert.Throws<ArgumentNullException>(() => d.Where(kv => true));
    }

    [Fact(DisplayName = "excluded が null だと d に要素がある場合に列挙時に NullReferenceException、空なら投げない")]
    public void NullExcludedThrowsOnlyWhenEnumeratingElements()
    {
        HashSet<string> excluded = null!;

        Assert.Empty(Omit(new Dictionary<string, int>(), excluded));

        var d = new Dictionary<string, int> { ["a"] = 1 };
        var deferred = d.Where(kv => !excluded.Contains(kv.Key));
        Assert.Throws<NullReferenceException>(() => deferred.ToDictionary());
    }
}
