// カード number-round-to の Contract を検証するテスト
package examples

import (
	"fmt"
	"math"
	"testing"
)

func roundTo(x float64, digits int) float64 {
	p := math.Pow(10, float64(digits))
	return math.Round(x*p) / p
}

func TestNumberRoundTo(t *testing.T) {
	t.Run(".5 は 0 から遠い方へ丸める", func(t *testing.T) {
		cases := map[float64]float64{2.5: 3, -2.5: -3, 0.5: 1, 1.5: 2, 1.2345: 1}
		for in, want := range cases {
			if got := math.Round(in); got != want {
				t.Errorf("math.Round(%v) = %v, want %v", in, got, want)
			}
		}
	})

	t.Run("桁指定のイディオム。負の桁は 10 の位・100 の位で丸める", func(t *testing.T) {
		cases := []struct {
			x      float64
			digits int
			want   float64
		}{{1.2345, 2, 1.23}, {1.2345, 0, 1}, {1250, -2, 1300}, {1350, -2, 1400}, {1234.5678, -2, 1200}, {2.5, 0, 3}, {-2.5, 0, -3}, {3, 2, 3}}
		for _, c := range cases {
			if got := roundTo(c.x, c.digits); got != c.want {
				t.Errorf("roundTo(%v, %d) = %v, want %v", c.x, c.digits, got, c.want)
			}
		}
	})

	t.Run("浮動小数点の補正はしない。1.005 は 1 になり 2.675 は 2.68 になる", func(t *testing.T) {
		x, y := 1.005, 2.675
		if got := roundTo(x, 2); got != 1 {
			t.Errorf("roundTo(1.005, 2) = %v", got)
		}
		if x*100 != 100.49999999999999 {
			t.Errorf("1.005*100 = %v", x*100)
		}
		if got := roundTo(y, 2); got != 2.68 {
			t.Errorf("roundTo(2.675, 2) = %v", got)
		}
	})

	t.Run("NaN と ±Inf はそのまま、-0.4 は -0", func(t *testing.T) {
		if got := roundTo(math.NaN(), 2); !math.IsNaN(got) {
			t.Errorf("NaN: %v", got)
		}
		if got := roundTo(math.Inf(1), 2); !math.IsInf(got, 1) {
			t.Errorf("+Inf: %v", got)
		}
		if got := roundTo(-0.4, 0); got != 0 || !math.Signbit(got) {
			t.Errorf("-0.4: %v signbit=%v", got, math.Signbit(got))
		}
	})

	t.Run("極端な桁数では NaN", func(t *testing.T) {
		if got := roundTo(1.5, 400); !math.IsNaN(got) {
			t.Errorf("digits=400: %v", got)
		}
		if got := roundTo(1.5, -400); !math.IsNaN(got) {
			t.Errorf("digits=-400: %v", got)
		}
	})

	t.Run("RoundToEven は偶数丸め、Sprintf は 2 進数の値を正しく丸める", func(t *testing.T) {
		if got := math.RoundToEven(2.5); got != 2 {
			t.Errorf("RoundToEven(2.5) = %v", got)
		}
		if got := math.RoundToEven(-2.5); got != -2 {
			t.Errorf("RoundToEven(-2.5) = %v", got)
		}
		if got := fmt.Sprintf("%.2f", 2.675); got != "2.67" {
			t.Errorf("Sprintf(2.675) = %q", got)
		}
		if got := fmt.Sprintf("%.0f", 2.5); got != "2" {
			t.Errorf("Sprintf(2.5) = %q", got)
		}
		z := 1.45
		if got := fmt.Sprintf("%.1f", z); got != "1.4" {
			t.Errorf("Sprintf(1.45) = %q", got)
		}
		if got := roundTo(z, 1); got != 1.5 {
			t.Errorf("roundTo(1.45, 1) = %v", got)
		}
	})

	t.Run("定数だけの式はコンパイル時に任意精度で計算される", func(t *testing.T) {
		if got := math.Round(1.005*100) / 100; got != 1.01 {
			t.Errorf("リテラル: %v", got)
		}
		x := 1.005
		if got := math.Round(x*100) / 100; got != 1 {
			t.Errorf("変数: %v", got)
		}
	})
}
