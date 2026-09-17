// カード date-format-iso の Contract を検証するテスト
package examples

import (
	"encoding/json"
	"testing"
	"time"
)

func TestDateFormatISO(t *testing.T) {
	tokyo, err := time.LoadLocation("Asia/Tokyo")
	if err != nil {
		t.Fatal(err)
	}
	d := time.Date(2024, 2, 29, 13, 45, 7, 123456789, tokyo)

	t.Run("Location のオフセットを付け、オフセット 0 のときだけ Z", func(t *testing.T) {
		if got := d.Format(time.RFC3339); got != "2024-02-29T13:45:07+09:00" {
			t.Errorf("JST = %q", got)
		}
		if got := d.UTC().Format(time.RFC3339); got != "2024-02-29T04:45:07Z" {
			t.Errorf("UTC = %q", got)
		}
		if got := d.In(time.FixedZone("", 0)).Format(time.RFC3339); got != "2024-02-29T04:45:07Z" {
			t.Errorf("FixedZone(0) = %q", got)
		}
		if got := d.In(time.FixedZone("", -3*3600-30*60)).Format(time.RFC3339); got != "2024-02-29T01:15:07-03:30" {
			t.Errorf("-03:30 = %q", got)
		}
	})

	t.Run("RFC3339 はナノ秒を捨て、RFC3339Nano は末尾の 0 を除いた小数秒を出す", func(t *testing.T) {
		if got := d.Format(time.RFC3339Nano); got != "2024-02-29T13:45:07.123456789+09:00" {
			t.Errorf("Nano = %q", got)
		}
		d12 := time.Date(2024, 2, 29, 13, 45, 7, 120000000, tokyo)
		if got := d12.Format(time.RFC3339Nano); got != "2024-02-29T13:45:07.12+09:00" {
			t.Errorf("Nano(.12) = %q", got)
		}
		d0 := time.Date(2024, 2, 29, 13, 45, 7, 0, tokyo)
		if got := d0.Format(time.RFC3339Nano); got != "2024-02-29T13:45:07+09:00" {
			t.Errorf("Nano(0) = %q", got)
		}
		if got := d.Format("2006-01-02T15:04:05.000Z07:00"); got != "2024-02-29T13:45:07.123+09:00" {
			t.Errorf("固定桁 = %q", got)
		}
		if got := d.Format(time.DateOnly); got != "2024-02-29" {
			t.Errorf("DateOnly = %q", got)
		}
	})

	t.Run("年は 4 桁ゼロ埋め、5 桁以上や負の年はそのまま", func(t *testing.T) {
		if got := time.Date(999, 1, 1, 0, 0, 0, 0, time.UTC).Format(time.RFC3339); got != "0999-01-01T00:00:00Z" {
			t.Errorf("999 = %q", got)
		}
		if got := time.Date(12345, 1, 1, 0, 0, 0, 0, time.UTC).Format(time.RFC3339); got != "12345-01-01T00:00:00Z" {
			t.Errorf("12345 = %q", got)
		}
		if got := time.Date(-1, 1, 1, 0, 0, 0, 0, time.UTC).Format(time.RFC3339); got != "-0001-01-01T00:00:00Z" {
			t.Errorf("-1 = %q", got)
		}
	})

	t.Run("ゼロ値は 0001-01-01T00:00:00Z", func(t *testing.T) {
		if got := (time.Time{}).Format(time.RFC3339); got != "0001-01-01T00:00:00Z" {
			t.Errorf("zero = %q", got)
		}
	})

	t.Run("入力を変更しない", func(t *testing.T) {
		before := d
		_ = d.Format(time.RFC3339)
		if !d.Equal(before) || d.Nanosecond() != 123456789 {
			t.Errorf("入力が変更された: %v", d)
		}
	})

	t.Run("Parse で同じ瞬間に戻るが Location は元の *Location ではない", func(t *testing.T) {
		p, err := time.Parse(time.RFC3339, d.Format(time.RFC3339))
		if err != nil {
			t.Fatal(err)
		}
		if !p.Equal(d.Truncate(time.Second)) {
			t.Errorf("Parse = %v", p)
		}
		if p.Equal(d) {
			t.Errorf("ナノ秒が切り捨てられるので Equal にならないはず")
		}
		if p.Location() == tokyo {
			t.Errorf("Location が元と同じポインタ")
		}
		if _, off := p.Zone(); off != 9*3600 {
			t.Errorf("オフセット = %d", off)
		}
		pl, err := time.ParseInLocation(time.RFC3339, d.Format(time.RFC3339), tokyo)
		if err != nil || pl.Location() != tokyo {
			t.Errorf("ParseInLocation: %v %v", pl.Location(), err)
		}
		pn, _ := time.Parse(time.RFC3339Nano, d.Format(time.RFC3339Nano))
		if !pn.Equal(d) {
			t.Errorf("RFC3339Nano の往復 = %v", pn)
		}
	})

	t.Run("json は RFC3339Nano、-07:00 レイアウトは UTC でも +00:00", func(t *testing.T) {
		b, err := json.Marshal(d)
		if err != nil || string(b) != `"2024-02-29T13:45:07.123456789+09:00"` {
			t.Errorf("json = %s %v", b, err)
		}
		if got := d.UTC().Format("2006-01-02T15:04:05-07:00"); got != "2024-02-29T04:45:07+00:00" {
			t.Errorf("-07:00 = %q", got)
		}
	})
}
