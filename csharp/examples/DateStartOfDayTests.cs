public class DateStartOfDayTests
{
    [Fact(DisplayName = "時刻部分を 00:00:00.0000000 にし、日付は変えない")]
    public void TruncatesTime()
    {
        var d = new DateTime(2024, 2, 29, 13, 45, 7, 123).AddTicks(4567);
        Assert.Equal(new DateTime(2024, 2, 29), d.Date);
        Assert.Equal(TimeSpan.Zero, d.Date.TimeOfDay);
        Assert.Equal(new DateTime(2024, 2, 29), new DateTime(2024, 2, 29, 23, 59, 59).AddTicks(9999999).Date);
    }

    [Fact(DisplayName = "Kind を保つ")]
    public void PreservesKind()
    {
        Assert.Equal(DateTimeKind.Local, new DateTime(2024, 2, 29, 13, 0, 0, DateTimeKind.Local).Date.Kind);
        Assert.Equal(DateTimeKind.Utc, new DateTime(2024, 2, 29, 13, 0, 0, DateTimeKind.Utc).Date.Kind);
        Assert.Equal(DateTimeKind.Unspecified, new DateTime(2024, 2, 29, 13, 0, 0).Date.Kind);
    }

    [Fact(DisplayName = "入力を変更せず、冪等")]
    public void ImmutableAndIdempotent()
    {
        var d = new DateTime(2024, 2, 29, 13, 45, 7, DateTimeKind.Local);
        var start = d.Date;
        Assert.Equal(13, d.Hour);
        Assert.Equal(start, start.Date);
    }

    [Fact(DisplayName = "壁時計の日付で丸めるので UTC の値は UTC の日付になる")]
    public void UsesWallClockOfTheValue()
    {
        var utc = new DateTime(2024, 2, 28, 20, 0, 0, DateTimeKind.Utc);
        Assert.Equal(new DateTime(2024, 2, 28, 0, 0, 0, DateTimeKind.Utc), utc.Date);
        var tokyo = TimeZoneInfo.FindSystemTimeZoneById("Asia/Tokyo");
        Assert.Equal(new DateTime(2024, 2, 29), TimeZoneInfo.ConvertTimeFromUtc(utc, tokyo).Date);
    }

    [Fact(DisplayName = "DateTimeOffset.Date は Kind Unspecified の DateTime を返しオフセットが落ちる")]
    public void DateTimeOffsetDateDropsOffset()
    {
        var o = new DateTimeOffset(2024, 2, 29, 1, 45, 7, TimeSpan.FromHours(9));
        Assert.Equal(DateTimeKind.Unspecified, o.Date.Kind);
        Assert.Equal(new DateTime(2024, 2, 29), o.Date);
        Assert.Equal(new DateTime(2024, 2, 28), o.UtcDateTime.Date);
        Assert.Equal(new DateTimeOffset(2024, 2, 29, 0, 0, 0, TimeSpan.FromHours(9)), new DateTimeOffset(o.Date, o.Offset));
    }

    [Fact(DisplayName = "例外は投げず、MinValue の Date は MinValue")]
    public void NeverThrows()
    {
        Assert.Equal(DateTime.MinValue, DateTime.MinValue.Date);
        Assert.Equal(new DateTime(9999, 12, 31), DateTime.MaxValue.Date);
    }

    [Fact(DisplayName = "DateOnly への変換・タイムゾーン変換・翌日 0 時を上限にした範囲判定")]
    public void Alternatives()
    {
        var o = new DateTimeOffset(2024, 2, 29, 1, 45, 7, TimeSpan.FromHours(9));
        Assert.Equal(new DateOnly(2024, 2, 29), DateOnly.FromDateTime(o.Date));
        var newYork = TimeZoneInfo.FindSystemTimeZoneById("America/New_York");
        Assert.Equal(new DateTime(2024, 2, 28), TimeZoneInfo.ConvertTime(o, newYork).Date);
        var d = new DateTime(2024, 2, 29, 23, 59, 59, 999);
        var start = d.Date;
        var end = start.AddDays(1);
        Assert.True(start <= d && d < end);
        Assert.Equal(DateTimeKind.Local, DateTime.Today.Kind);
    }
}
