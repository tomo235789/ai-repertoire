public class DateDiffDaysTests
{
    private static readonly DateTime Later = new(2024, 3, 1, 0, 1, 0);
    private static readonly DateTime Earlier = new(2024, 2, 29, 23, 59, 0);

    [Fact(DisplayName = ".Date で時刻を落としてから引くと暦日差になる")]
    public void CalendarDayDifference()
    {
        Assert.Equal(1, (Later.Date - Earlier.Date).Days);
        Assert.Equal(-1, (Earlier.Date - Later.Date).Days);
        Assert.Equal(0, (Later.Date - Later.AddHours(20).Date).Days);
        Assert.Equal(365, (new DateTime(2025, 3, 1) - new DateTime(2024, 3, 1)).Days);
        Assert.Equal(366, (new DateTime(2025, 2, 28) - new DateTime(2024, 2, 28)).Days);
    }

    [Fact(DisplayName = ".Date 無しの TimeSpan.Days は経過時間をゼロ方向に切り捨てる")]
    public void RawDaysTruncatesTowardZero()
    {
        Assert.Equal(0, (Later - Earlier).Days);
        Assert.Equal(0, (Earlier - Later).Days);
        Assert.Equal(0, (Earlier - Earlier.AddHours(12)).Days);
        Assert.Equal(1, (Earlier.AddHours(36) - Earlier).Days);
        Assert.Equal(-1, (Earlier - Earlier.AddHours(36)).Days);
    }

    [Fact(DisplayName = "TotalDays は小数を含む実時間の日数")]
    public void TotalDaysIsFractional()
    {
        Assert.Equal(-0.5, (Earlier - Earlier.AddHours(12)).TotalDays);
        Assert.Equal(1.5, (Earlier.AddHours(36) - Earlier).TotalDays);
    }

    [Fact(DisplayName = "Kind が違っても補正されず壁時計の値同士で引かれる")]
    public void KindIsNotAdjusted()
    {
        var utc = new DateTime(2024, 3, 1, 0, 0, 0, DateTimeKind.Utc);
        var local = new DateTime(2024, 3, 1, 0, 0, 0, DateTimeKind.Local);
        Assert.Equal(TimeSpan.Zero, utc - local);
    }

    [Fact(DisplayName = "入力を変更せず、最大範囲でも例外を出さない")]
    public void DoesNotMutateAndNeverThrows()
    {
        var a = Later;
        var b = Earlier;
        _ = a.Date - b.Date;
        Assert.Equal(Later, a);
        Assert.Equal(Earlier, b);
        Assert.Equal(3652058, (DateTime.MaxValue - DateTime.MinValue).Days);
    }

    [Fact(DisplayName = "DateTimeOffset の減算は実時間、.Date はそれぞれのオフセットのローカル日付")]
    public void DateTimeOffsetSubtraction()
    {
        var jst = new DateTimeOffset(2024, 3, 1, 0, 30, 0, TimeSpan.FromHours(9));
        var utc = new DateTimeOffset(2024, 2, 29, 20, 0, 0, TimeSpan.Zero);
        Assert.Equal(-4.5, (jst - utc).TotalHours);
        Assert.Equal(DateTimeKind.Unspecified, jst.Date.Kind);
        Assert.Equal(1, (jst.Date - utc.Date).Days);
        Assert.Equal(0, (jst.UtcDateTime.Date - utc.UtcDateTime.Date).Days);
    }

    [Fact(DisplayName = "DateOnly の DayNumber 差と同じ日かの判定")]
    public void Alternatives()
    {
        Assert.Equal(1, DateOnly.FromDateTime(Later).DayNumber - DateOnly.FromDateTime(Earlier).DayNumber);
        Assert.False(Later.Date == Earlier.Date);
        Assert.True(Later.Date == Later.AddHours(23).Date);
    }
}
