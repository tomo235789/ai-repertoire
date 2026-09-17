// カード date-start-of-day の Contract を検証するテスト
package examples

import (
	"testing"
	"time"
)

func startOfDay(t time.Time) time.Time {
	y, m, d := t.Date()
	s := time.Date(y, m, d, 0, 0, 0, 0, t.Location())
	if s.Day() != d { // 0 時が存在しない日は前日 23 時に正規化されるので、その日の最初の時刻へ進める
		s = s.Add(time.Hour)
	}
	return s
}

func TestDateStartOfDay(t *testing.T) {
	tokyo, err := time.LoadLocation("Asia/Tokyo")
	if err != nil {
		t.Fatal(err)
	}
	ny, err := time.LoadLocation("America/New_York")
	if err != nil {
		t.Fatal(err)
	}
	d := time.Date(2024, 2, 29, 13, 45, 7, 123456789, tokyo)

	t.Run("同じ Location の同じ日の 0 時にする", func(t *testing.T) {
		got := startOfDay(d)
		if !got.Equal(time.Date(2024, 2, 29, 0, 0, 0, 0, tokyo)) {
			t.Errorf("startOfDay = %v", got)
		}
		if got.Location() != tokyo || got.Nanosecond() != 0 {
			t.Errorf("Location / ナノ秒 = %v %d", got.Location(), got.Nanosecond())
		}
	})

	t.Run("入力を変更しない", func(t *testing.T) {
		startOfDay(d)
		if d.Hour() != 13 || d.Nanosecond() != 123456789 {
			t.Errorf("入力が変更された: %v", d)
		}
	})

	t.Run("冪等", func(t *testing.T) {
		if !startOfDay(startOfDay(d)).Equal(startOfDay(d)) {
			t.Errorf("冪等でない")
		}
	})

	t.Run("Location だけで決まり、同じ瞬間でも Location が違えば別の瞬間になる", func(t *testing.T) {
		inNY := startOfDay(d.In(ny))
		if inNY.Format("2006-01-02 15:04 MST") != "2024-02-28 00:00 EST" {
			t.Errorf("NY = %v", inNY)
		}
		if inNY.Equal(startOfDay(d)) {
			t.Errorf("別の瞬間になるはず")
		}
		if got := startOfDay(d.In(time.UTC)); !got.Equal(time.Date(2024, 2, 29, 0, 0, 0, 0, time.UTC)) {
			t.Errorf("UTC = %v", got)
		}
	})

	t.Run("ゼロ値はゼロ値のまま", func(t *testing.T) {
		if got := startOfDay(time.Time{}); !got.IsZero() || got.Location() != time.UTC {
			t.Errorf("zero = %v", got)
		}
	})

	t.Run("0 時が存在しない日（Sao Paulo 2018-11-04）はその日の最初の時刻 01:00 -02 を返し冪等", func(t *testing.T) {
		sp, err := time.LoadLocation("America/Sao_Paulo")
		if err != nil {
			t.Skip("tzdata なし")
		}
		got := startOfDay(time.Date(2018, 11, 4, 12, 0, 0, 0, sp))
		if got.Day() != 4 || got.Hour() != 1 {
			t.Errorf("Sao Paulo = %v", got)
		}
		if !startOfDay(got).Equal(got) {
			t.Errorf("not idempotent: %v", startOfDay(got))
		}
		// 補正無しの time.Date がどちらのオフセットで解釈するかは未規定。前日 23:00 -03 か当日 01:00 -02 のどちらか
		raw := time.Date(2018, 11, 4, 0, 0, 0, 0, sp)
		if !raw.Add(time.Hour).Equal(got) && !raw.Equal(got) {
			t.Errorf("raw = %v", raw)
		}
	})

	t.Run("Truncate(24h) は UTC 基準なので 0 時にならない", func(t *testing.T) {
		got := d.Truncate(24 * time.Hour)
		if got.Format("2006-01-02 15:04 MST") != "2024-02-29 09:00 JST" {
			t.Errorf("Truncate = %v", got)
		}
		if got.Equal(startOfDay(d)) {
			t.Errorf("Truncate と startOfDay が一致してしまう")
		}
	})
}
