// カード date-diff-days の Contract を検証するテスト
package examples

import (
	"math"
	"testing"
	"time"
)

func diffDays(later, earlier time.Time) int {
	l := time.Date(later.Year(), later.Month(), later.Day(), 0, 0, 0, 0, time.UTC)
	e := time.Date(earlier.Year(), earlier.Month(), earlier.Day(), 0, 0, 0, 0, time.UTC)
	return int(l.Sub(e).Hours() / 24)
}

func TestDateDiffDays(t *testing.T) {
	tokyo, err := time.LoadLocation("Asia/Tokyo")
	if err != nil {
		t.Fatal(err)
	}
	ny, err := time.LoadLocation("America/New_York")
	if err != nil {
		t.Fatal(err)
	}
	later := time.Date(2024, 3, 1, 0, 1, 0, 0, tokyo)
	earlier := time.Date(2024, 2, 29, 23, 59, 0, 0, tokyo)

	t.Run("後の日付、前の日付の順で暦日差。逆順なら負、同じ日なら 0", func(t *testing.T) {
		if got := diffDays(later, earlier); got != 1 {
			t.Errorf("later - earlier = %d", got)
		}
		if got := diffDays(earlier, later); got != -1 {
			t.Errorf("earlier - later = %d", got)
		}
		if got := diffDays(later, later); got != 0 {
			t.Errorf("同じ日 = %d", got)
		}
		if got := diffDays(time.Date(2025, 3, 1, 0, 0, 0, 0, tokyo), time.Date(2024, 3, 1, 0, 0, 0, 0, tokyo)); got != 365 {
			t.Errorf("1 年 = %d", got)
		}
	})

	t.Run("時刻は無視される。実時間の差は 2 分", func(t *testing.T) {
		if got := later.Sub(earlier); got != 2*time.Minute {
			t.Errorf("Sub = %v", got)
		}
		if got := int(later.Sub(earlier).Hours() / 24); got != 0 {
			t.Errorf("実時間ベース = %d", got)
		}
	})

	t.Run("DST 切替日（実時間 23 時間）でも暦日差は 1", func(t *testing.T) {
		d0 := time.Date(2024, 3, 10, 0, 0, 0, 0, ny)
		d1 := time.Date(2024, 3, 11, 0, 0, 0, 0, ny)
		if got := d1.Sub(d0); got != 23*time.Hour {
			t.Errorf("Sub = %v", got)
		}
		if got := diffDays(d1, d0); got != 1 {
			t.Errorf("diffDays = %d", got)
		}
		if got := int(d1.Sub(d0).Hours() / 24); got != 0 {
			t.Errorf("切り捨て = %d", got)
		}
	})

	t.Run("Sub は約 292 年で飽和する", func(t *testing.T) {
		base := time.Date(2000, 1, 1, 0, 0, 0, 0, time.UTC)
		if got := time.Date(2292, 1, 1, 0, 0, 0, 0, time.UTC).Sub(base); got == time.Duration(math.MaxInt64) {
			t.Errorf("292 年は飽和しないはず")
		}
		if got := time.Date(2293, 1, 1, 0, 0, 0, 0, time.UTC).Sub(base); got != time.Duration(math.MaxInt64) {
			t.Errorf("293 年 = %v", got)
		}
	})

	t.Run("Location が違うとそれぞれのローカル日付で比べる", func(t *testing.T) {
		jst := time.Date(2024, 3, 1, 0, 30, 0, 0, tokyo)
		utc := time.Date(2024, 2, 29, 20, 0, 0, 0, time.UTC)
		if got := diffDays(jst, utc); got != 1 {
			t.Errorf("混在 = %d", got)
		}
		if got := diffDays(jst.In(time.UTC), utc); got != 0 {
			t.Errorf("UTC に揃えた = %d", got)
		}
	})

	t.Run("UTC+14 と UTC-12 で同じローカル日付なら、実時間が離れていても 0", func(t *testing.T) {
		plus14 := time.Date(2024, 3, 1, 23, 0, 0, 0, time.FixedZone("UTC+14", 14*3600))
		minus12 := time.Date(2024, 3, 1, 0, 0, 0, 0, time.FixedZone("UTC-12", -12*3600))
		if got := diffDays(plus14, minus12); got != 0 {
			t.Errorf("+14 - (-12) = %d", got)
		}
		if got := diffDays(minus12, plus14); got != 0 {
			t.Errorf("-12 - (+14) = %d", got)
		}
	})

	t.Run("入力を変更せず、ゼロ値も扱える", func(t *testing.T) {
		before := later
		diffDays(later, earlier)
		if !later.Equal(before) {
			t.Errorf("入力が変更された")
		}
		if got := diffDays(time.Date(1, 1, 2, 0, 0, 0, 0, time.UTC), time.Time{}); got != 1 {
			t.Errorf("zero = %d", got)
		}
	})

	t.Run("日付をスキップするゾーン（Pacific/Apia 2011-12-30）でも暦日差は日付の差", func(t *testing.T) {
		apia, err := time.LoadLocation("Pacific/Apia")
		if err != nil {
			t.Skip("tzdata なし")
		}
		a := time.Date(2011, 12, 29, 12, 0, 0, 0, apia)
		b := time.Date(2011, 12, 31, 12, 0, 0, 0, apia)
		if got := diffDays(b, a); got != 2 {
			t.Errorf("diffDays = %d, want 2", got)
		}
	})

}
