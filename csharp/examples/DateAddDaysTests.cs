public class DateAddDaysTests
{
    private static readonly DateTime Base = new(2024, 2, 29, 13, 45, 0);

    [Fact(DisplayName = "日数を足した新しい値を返し、負数なら減算になる")]
    public void AddsAndSubtractsDays()
    {
        Assert.Equal(new DateTime(2024, 3, 1, 13, 45, 0), Base.AddDays(1));
        Assert.Equal(new DateTime(2024, 2, 28, 13, 45, 0), Base.AddDays(-1));
    }

    [Fact(DisplayName = "入力は変更されない")]
    public void DoesNotMutateInput()
    {
        var d = Base;
        d.AddDays(5);
        Assert.Equal(Base, d);
    }

    [Fact(DisplayName = "月末・年末・うるう年の繰り越しはカレンダーどおり")]
    public void CalendarCarry()
    {
        Assert.Equal(new DateTime(2025, 3, 1, 13, 45, 0), Base.AddDays(366));
        Assert.Equal(new DateTime(2025, 2, 28, 13, 45, 0), Base.AddDays(365));
        Assert.Equal(new DateTime(2025, 1, 1), new DateTime(2024, 12, 31).AddDays(1));
    }

    [Fact(DisplayName = "時刻・ティック・Kind は保たれる")]
    public void PreservesTimeAndKind()
    {
        var utc = new DateTime(2024, 2, 29, 13, 45, 7, 123, DateTimeKind.Utc).AddTicks(4567);
        var result = utc.AddDays(1);
        Assert.Equal(utc.TimeOfDay, result.TimeOfDay);
        Assert.Equal(DateTimeKind.Utc, result.Kind);
        Assert.Equal(DateTimeKind.Local, new DateTime(2024, 2, 29, 0, 0, 0, DateTimeKind.Local).AddDays(1).Kind);
        Assert.Equal(DateTimeKind.Unspecified, Base.AddDays(1).Kind);
    }

    [Fact(DisplayName = "小数は時間に換算される（1.5 日 = 36 時間）")]
    public void FractionalDaysBecomeHours()
    {
        Assert.Equal(new DateTime(2024, 3, 2, 1, 45, 0), Base.AddDays(1.5));
        Assert.Equal(new DateTime(2024, 2, 28, 1, 45, 0), Base.AddDays(-1.5));
        Assert.Equal(Base + TimeSpan.FromDays(0.5), Base.AddDays(0.5));
        Assert.Equal(TimeSpan.FromHours(36), Base.AddDays(1.5) - Base);
    }

    [Fact(DisplayName = "壁時計をそのまま進めるので DST 切替をまたぐと実時間は 23 時間になる")]
    public void WallClockIgnoresDst()
    {
        var tz = TimeZoneInfo.FindSystemTimeZoneById("America/New_York"); // 2024-03-10 02:00 に DST 開始
        var before = new DateTime(2024, 3, 9, 12, 0, 0);
        var after = before.AddDays(1);
        Assert.Equal(new DateTime(2024, 3, 10, 12, 0, 0), after);
        var elapsed = TimeZoneInfo.ConvertTimeToUtc(after, tz) - TimeZoneInfo.ConvertTimeToUtc(before, tz);
        Assert.Equal(TimeSpan.FromHours(23), elapsed);
    }

    [Fact(DisplayName = "範囲外や無限大は ArgumentOutOfRangeException")]
    public void OutOfRangeThrows()
    {
        Assert.Throws<ArgumentOutOfRangeException>(() => DateTime.MaxValue.AddDays(1));
        Assert.Throws<ArgumentOutOfRangeException>(() => DateTime.MinValue.AddDays(-1));
        Assert.Throws<ArgumentOutOfRangeException>(() => Base.AddDays(double.PositiveInfinity));
        Assert.Throws<ArgumentOutOfRangeException>(() => Base.AddDays(1e9));
    }

    [Fact(DisplayName = "DateTimeOffset.AddDays はオフセット固定で実時間は常に 24 時間 × 日数")]
    public void DateTimeOffsetKeepsOffset()
    {
        var o = new DateTimeOffset(2024, 3, 9, 12, 0, 0, TimeSpan.FromHours(-5));
        var next = o.AddDays(1);
        Assert.Equal(TimeSpan.FromHours(-5), next.Offset);
        Assert.Equal(TimeSpan.FromHours(24), next - o);
    }

    [Fact(DisplayName = "TimeSpan の加算・AddMonths の月末クランプ・DateOnly.AddDays")]
    public void Alternatives()
    {
        Assert.Equal(Base.AddDays(1.5), Base + TimeSpan.FromDays(1.5));
        Assert.Equal(Base.AddDays(-1), Base - TimeSpan.FromDays(1));
        Assert.Equal(new DateTime(2024, 2, 29), new DateTime(2024, 1, 31).AddMonths(1));
        Assert.Equal(new DateOnly(2024, 3, 1), new DateOnly(2024, 2, 29).AddDays(1));
    }
}
