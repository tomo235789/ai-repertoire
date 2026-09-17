using System.Globalization;
using System.Text.RegularExpressions;

public class DateFormatIsoTests
{
    private static readonly DateTimeOffset Sample = new(2024, 2, 29, 13, 45, 7, TimeSpan.FromHours(9));

    [Fact(DisplayName = "DateTimeOffset の o 書式は小数 7 桁とオフセット付きの ISO 8601 になる")]
    public void FormatsDateTimeOffset()
    {
        Assert.Equal("2024-02-29T13:45:07.0000000+09:00", Sample.ToString("o"));
        Assert.Equal("2024-02-29T13:45:07.1230000+09:00", Sample.AddMilliseconds(123).ToString("o"));
        Assert.Equal("2024-02-29T13:45:07.0000000-05:00", new DateTimeOffset(2024, 2, 29, 13, 45, 7, TimeSpan.FromHours(-5)).ToString("o"));
    }

    [Fact(DisplayName = "オフセット 0 は Z ではなく +00:00 になる")]
    public void ZeroOffsetIsPlusZero()
    {
        Assert.Equal("2024-02-29T13:45:07.0000000+00:00", new DateTimeOffset(2024, 2, 29, 13, 45, 7, TimeSpan.Zero).ToString("o"));
        Assert.Equal("2024-02-29T04:45:07.0000000Z", Sample.UtcDateTime.ToString("o"));
    }

    [Fact(DisplayName = "DateTime の o 書式は Kind によって末尾が変わる")]
    public void DateTimeSuffixDependsOnKind()
    {
        Assert.Equal("2024-02-29T13:45:07.0000000", new DateTime(2024, 2, 29, 13, 45, 7).ToString("o"));
        Assert.Equal("2024-02-29T13:45:07.0000000Z", new DateTime(2024, 2, 29, 13, 45, 7, DateTimeKind.Utc).ToString("o"));
        var local = new DateTime(2024, 2, 29, 13, 45, 7, DateTimeKind.Local);
        var text = local.ToString("o");
        Assert.Matches(new Regex(@"^2024-02-29T13:45:07\.0000000[+-]\d{2}:\d{2}$"), text);
        Assert.Equal(new DateTimeOffset(local).ToString("o"), text);
    }

    [Fact(DisplayName = "カルチャに依存しない")]
    public void CultureIndependent()
    {
        foreach (var name in new[] { "ja-JP", "ar-SA", "th-TH" })
        {
            var culture = CultureInfo.GetCultureInfo(name);
            Assert.Equal("2024-02-29T13:45:07.0000000+09:00", Sample.ToString("o", culture));
            var old = CultureInfo.CurrentCulture;
            CultureInfo.CurrentCulture = culture;
            try { Assert.Equal("2024-02-29T13:45:07.0000000+09:00", Sample.ToString("o")); }
            finally { CultureInfo.CurrentCulture = old; }
        }
    }

    [Fact(DisplayName = "年は 4 桁ゼロ埋め")]
    public void YearIsZeroPadded()
    {
        Assert.Equal("0001-01-01T00:00:00.0000000+00:00", DateTimeOffset.MinValue.ToString("o"));
    }

    [Fact(DisplayName = "DateTimeOffset.Parse / ParseExact で元の値とオフセットに戻る")]
    public void RoundTripsThroughDateTimeOffset()
    {
        var text = Sample.ToString("o");
        var parsed = DateTimeOffset.Parse(text, CultureInfo.InvariantCulture);
        Assert.Equal(Sample, parsed);
        Assert.Equal(TimeSpan.FromHours(9), parsed.Offset);
        Assert.Equal(Sample, DateTimeOffset.ParseExact(text, "o", CultureInfo.InvariantCulture));
    }

    [Fact(DisplayName = "DateTime.Parse はローカルに変換して Kind Local にし、RoundtripKind で Kind を保つ")]
    public void DateTimeParseConvertsUnlessRoundtripKind()
    {
        var utcText = "2024-02-29T13:45:07.0000000Z";
        Assert.Equal(DateTimeKind.Local, DateTime.Parse(utcText, CultureInfo.InvariantCulture).Kind);
        var kept = DateTime.Parse(utcText, CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind);
        Assert.Equal(DateTimeKind.Utc, kept.Kind);
        Assert.Equal(13, kept.Hour);
        Assert.Equal(DateTimeKind.Unspecified, DateTime.Parse("2024-02-29T13:45:07.0000000", CultureInfo.InvariantCulture, DateTimeStyles.RoundtripKind).Kind);
        Assert.Equal(DateTimeKind.Local, DateTime.Parse("2024-02-29T13:45:07.0000000+09:00", CultureInfo.InvariantCulture).Kind);
    }

    [Fact(DisplayName = "入力の struct は変更されない")]
    public void DoesNotMutate()
    {
        var d = Sample;
        d.ToString("o");
        Assert.Equal(Sample, d);
    }

    [Fact(DisplayName = "K 指定・s・u・DateOnly の書式")]
    public void OtherFormats()
    {
        Assert.Equal("2024-02-29T13:45:07+09:00", Sample.ToString("yyyy-MM-dd'T'HH:mm:ssK"));
        Assert.Equal("2024-02-29T13:45:07", new DateTime(2024, 2, 29, 13, 45, 7).ToString("yyyy-MM-dd'T'HH:mm:ssK"));
        Assert.Equal("2024-02-29T13:45:07", Sample.ToString("s"));
        Assert.Equal("2024-02-29 04:45:07Z", Sample.ToString("u"));
        Assert.Equal("2024-02-29", new DateOnly(2024, 2, 29).ToString("o"));
    }
}
