// カード date-add-days の Contract を検証するテスト
package examples

import (
	"testing"
	"time"
)

func TestDateAddDays(t *testing.T) {
	tokyo, err := time.LoadLocation("Asia/Tokyo")
	if err != nil {
		t.Fatal(err)
	}
	ny, err := time.LoadLocation("America/New_York")
	if err != nil {
		t.Fatal(err)
	}
	d := time.Date(2024, 2, 29, 13, 45, 0, 0, tokyo)

	t.Run("入力を変更せず新しい値を返す", func(t *testing.T) {
		got := d.AddDate(0, 0, 1)
		if !got.Equal(time.Date(2024, 3, 1, 13, 45, 0, 0, tokyo)) {
			t.Errorf("+1 = %v", got)
		}
		if !d.Equal(time.Date(2024, 2, 29, 13, 45, 0, 0, tokyo)) {
			t.Errorf("入力が変更された: %v", d)
		}
		if !d.AddDate(0, 0, 0).Equal(d) {
			t.Errorf("+0 が Equal でない")
		}
	})

	t.Run("月末・年末・うるう年の繰り越しはカレンダーどおり", func(t *testing.T) {
		if got := d.AddDate(0, 0, -1); !got.Equal(time.Date(2024, 2, 28, 13, 45, 0, 0, tokyo)) {
			t.Errorf("-1 = %v", got)
		}
		if got := d.AddDate(0, 0, 366); !got.Equal(time.Date(2025, 3, 1, 13, 45, 0, 0, tokyo)) {
			t.Errorf("+366 = %v", got)
		}
		if got := d.AddDate(0, 0, 365); !got.Equal(time.Date(2025, 2, 28, 13, 45, 0, 0, tokyo)) {
			t.Errorf("+365 = %v", got)
		}
		if got := time.Date(2024, 12, 31, 0, 0, 0, 0, tokyo).AddDate(0, 0, 1); got.Format(time.DateOnly) != "2025-01-01" {
			t.Errorf("年末 = %v", got)
		}
	})

	t.Run("壁時計で進めるので DST をまたぐと経過時間は 23 時間になる", func(t *testing.T) {
		base := time.Date(2024, 3, 9, 12, 0, 0, 0, ny)
		next := base.AddDate(0, 0, 1)
		if next.Format("2006-01-02 15:04 MST") != "2024-03-10 12:00 EDT" {
			t.Errorf("AddDate = %v", next)
		}
		if next.Sub(base) != 23*time.Hour {
			t.Errorf("Sub = %v", next.Sub(base))
		}
		if got := base.Add(24 * time.Hour); got.Format("2006-01-02 15:04 MST") != "2024-03-10 13:00 EDT" {
			t.Errorf("Add(24h) = %v", got)
		}
		end := time.Date(2024, 11, 2, 12, 0, 0, 0, ny)
		if got := end.AddDate(0, 0, 1).Sub(end); got != 25*time.Hour {
			t.Errorf("DST 終了 Sub = %v", got)
		}
	})

	t.Run("存在しない日付は翌月へ繰り越し、月末にクランプしない", func(t *testing.T) {
		if got := time.Date(2023, 1, 31, 0, 0, 0, 0, tokyo).AddDate(0, 1, 0); got.Format(time.DateOnly) != "2023-03-03" {
			t.Errorf("2023-01-31 + 1 か月 = %v", got)
		}
		if got := time.Date(2024, 1, 31, 0, 0, 0, 0, tokyo).AddDate(0, 1, 0); got.Format(time.DateOnly) != "2024-03-02" {
			t.Errorf("2024-01-31 + 1 か月 = %v", got)
		}
		if got := time.Date(2024, 2, 29, 0, 0, 0, 0, tokyo).AddDate(1, 0, 0); got.Format(time.DateOnly) != "2025-03-01" {
			t.Errorf("2024-02-29 + 1 年 = %v", got)
		}
		if got := time.Date(2024, 3, 0, 0, 0, 0, 0, tokyo); got.Format(time.DateOnly) != "2024-02-29" {
			t.Errorf("翌月 0 日 = %v", got)
		}
	})

	t.Run("DST で存在しない時刻に着地しても panic せずずれる（どちらのオフセットかは未規定）", func(t *testing.T) {
		got := time.Date(2024, 3, 9, 2, 30, 0, 0, ny).AddDate(0, 0, 1)
		s := got.Format("2006-01-02 15:04 MST")
		if s != "2024-03-10 01:30 EST" && s != "2024-03-10 03:30 EDT" {
			t.Errorf("gap = %v", got)
		}
	})

	t.Run("ゼロ値にも足せる", func(t *testing.T) {
		if got := (time.Time{}).AddDate(0, 0, 1); got.Format(time.RFC3339) != "0001-01-02T00:00:00Z" {
			t.Errorf("zero + 1 = %v", got)
		}
	})
}
