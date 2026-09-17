// カード number-clamp の Contract を検証するテスト
package examples

import (
	"cmp"
	"math"
	"testing"

	"github.com/samber/lo"
)

func clamp[T cmp.Ordered](x, lo, hi T) T { return min(max(x, lo), hi) }

func TestNumberClamp(t *testing.T) {
	t.Run("範囲を超えた値は境界値に置き換え、境界値は含む", func(t *testing.T) {
		if got := clamp(120, 0, 100); got != 100 {
			t.Errorf("clamp(120, 0, 100) = %v", got)
		}
		if got := clamp(-5, 0, 100); got != 0 {
			t.Errorf("clamp(-5, 0, 100) = %v", got)
		}
		if got := clamp(42, 0, 100); got != 42 {
			t.Errorf("clamp(42, 0, 100) = %v", got)
		}
		if got := clamp(0, 0, 100); got != 0 {
			t.Errorf("clamp(0, 0, 100) = %v", got)
		}
		if got := clamp(100, 0, 100); got != 100 {
			t.Errorf("clamp(100, 0, 100) = %v", got)
		}
	})

	t.Run("cmp.Ordered なら浮動小数点・文字列でも使え、定数は型推論で揃う", func(t *testing.T) {
		if got := clamp(2.5, 0, 1); got != 1.0 {
			t.Errorf("clamp(2.5, 0, 1) = %v", got)
		}
		if got := clamp("m", "a", "z"); got != "m" {
			t.Errorf("clamp(\"m\", \"a\", \"z\") = %q", got)
		}
		if got := clamp("A", "a", "z"); got != "a" {
			t.Errorf("clamp(\"A\", \"a\", \"z\") = %q", got)
		}
	})

	t.Run("lo > hi なら常に hi を返す", func(t *testing.T) {
		for _, x := range []int{1, 10, 100} {
			if got := clamp(x, 15, 5); got != 5 {
				t.Errorf("clamp(%d, 15, 5) = %v", x, got)
			}
		}
	})

	t.Run("どれか 1 つでも NaN なら NaN", func(t *testing.T) {
		nan := math.NaN()
		if got := clamp(nan, 0, 100); !math.IsNaN(got) {
			t.Errorf("x が NaN: %v", got)
		}
		if got := clamp(5.0, nan, 100); !math.IsNaN(got) {
			t.Errorf("lo が NaN: %v", got)
		}
		if got := clamp(5.0, 0, nan); !math.IsNaN(got) {
			t.Errorf("hi が NaN: %v", got)
		}
	})

	t.Run("lo.Clamp は lo > hi のとき x < lo なら lo を返し、境界の NaN は無視する", func(t *testing.T) {
		if got := lo.Clamp(1, 15, 5); got != 15 {
			t.Errorf("lo.Clamp(1, 15, 5) = %v", got)
		}
		if got := lo.Clamp(100, 15, 5); got != 5 {
			t.Errorf("lo.Clamp(100, 15, 5) = %v", got)
		}
		if got := lo.Clamp(5.0, math.NaN(), 100); got != 5 {
			t.Errorf("lo.Clamp(5, NaN, 100) = %v", got)
		}
		if got := lo.Clamp(math.NaN(), 0, 100); !math.IsNaN(got) {
			t.Errorf("lo.Clamp(NaN, 0, 100) = %v", got)
		}
	})
}
