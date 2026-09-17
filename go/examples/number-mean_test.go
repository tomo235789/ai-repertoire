// カード number-mean の Contract を検証するテスト
package examples

import (
	"math"
	"slices"
	"testing"

	"github.com/samber/lo"
)

func TestNumberMean(t *testing.T) {
	t.Run("算術平均を返し、入力を変更しない", func(t *testing.T) {
		src := []float64{1, 2, 3, 4, 5}
		if got := lo.Mean(src); got != 3 {
			t.Errorf("Mean = %v", got)
		}
		if !slices.Equal(src, []float64{1, 2, 3, 4, 5}) {
			t.Errorf("入力が変更された: %v", src)
		}
		if got := lo.Mean([]float64{1, 2}); got != 1.5 {
			t.Errorf("Mean([1, 2]) = %v", got)
		}
	})

	t.Run("空スライスと nil は 0 を返し panic しない", func(t *testing.T) {
		if got := lo.Mean([]float64{}); got != 0 {
			t.Errorf("空 = %v", got)
		}
		if got := lo.Mean[int](nil); got != 0 {
			t.Errorf("nil = %v", got)
		}
	})

	t.Run("整数型は整数除算でゼロ方向に切り捨てる", func(t *testing.T) {
		if got := lo.Mean([]int{1, 2}); got != 1 {
			t.Errorf("[1, 2] = %v", got)
		}
		if got := lo.Mean([]int{1, 2, 4}); got != 2 {
			t.Errorf("[1, 2, 4] = %v", got)
		}
		if got := lo.Mean([]int{-7, -8}); got != -7 {
			t.Errorf("[-7, -8] = %v", got)
		}
	})

	t.Run("整数型は合計のオーバーフローを検出しない", func(t *testing.T) {
		if got := lo.Mean([]int8{100, 100}); got != -28 {
			t.Errorf("int8 = %v", got)
		}
	})

	t.Run("NaN や Inf の伝播", func(t *testing.T) {
		if got := lo.Mean([]float64{1, math.NaN()}); !math.IsNaN(got) {
			t.Errorf("NaN = %v", got)
		}
		if got := lo.Mean([]float64{math.Inf(1), math.Inf(-1)}); !math.IsNaN(got) {
			t.Errorf("+Inf/-Inf = %v", got)
		}
		if got := lo.Mean([]float64{math.Inf(1), 1}); !math.IsInf(got, 1) {
			t.Errorf("+Inf/1 = %v", got)
		}
	})

	t.Run("浮動小数点の誤差はそのまま", func(t *testing.T) {
		if got := lo.Mean([]float64{0.1, 0.2, 0.3}); got != 0.20000000000000004 {
			t.Errorf("Mean = %v", got)
		}
	})

	t.Run("MeanBy で float64 を返せば整数除算を避けられる", func(t *testing.T) {
		if got := lo.MeanBy([]int{1, 2}, func(x int) float64 { return float64(x) }); got != 1.5 {
			t.Errorf("MeanBy = %v", got)
		}
	})
}
