// カード number-sum-by の Contract を検証するテスト
package examples

import (
	"math"
	"slices"
	"testing"

	"github.com/samber/lo"
)

type sumItem struct {
	Name string
	Qty  int
}

func TestNumberSumBy(t *testing.T) {
	items := []sumItem{{"a", 2}, {"b", 3}}

	t.Run("各要素から取り出した数値を合計し、入力を変更しない", func(t *testing.T) {
		if got := lo.SumBy(items, func(i sumItem) int { return i.Qty }); got != 5 {
			t.Errorf("SumBy = %v", got)
		}
		if !slices.Equal(items, []sumItem{{"a", 2}, {"b", 3}}) {
			t.Errorf("入力が変更された: %v", items)
		}
	})

	t.Run("iteratee は各要素につき 1 回、先頭から順に呼ばれる", func(t *testing.T) {
		var order []string
		lo.SumBy(items, func(i sumItem) int { order = append(order, i.Name); return i.Qty })
		if !slices.Equal(order, []string{"a", "b"}) {
			t.Errorf("呼び出し順 = %v", order)
		}
	})

	t.Run("空スライスと nil は 0", func(t *testing.T) {
		if got := lo.SumBy([]sumItem{}, func(i sumItem) int { return i.Qty }); got != 0 {
			t.Errorf("空 = %v", got)
		}
		if got := lo.SumBy(nil, func(i sumItem) float64 { return 1 }); got != 0 {
			t.Errorf("nil = %v", got)
		}
	})

	t.Run("整数のオーバーフローは検出されず型の幅で巻き戻る", func(t *testing.T) {
		if got := lo.SumBy([]int8{100, 100}, func(i int8) int8 { return i }); got != -56 {
			t.Errorf("int8 = %v", got)
		}
		if got := lo.SumBy([]uint8{200, 100}, func(i uint8) uint8 { return i }); got != 44 {
			t.Errorf("uint8 = %v", got)
		}
		if got := lo.SumBy([]int64{math.MaxInt64, 1}, func(i int64) int64 { return i }); got != math.MinInt64 {
			t.Errorf("int64 = %v", got)
		}
	})

	t.Run("浮動小数点は誤差がそのままで、NaN があれば NaN", func(t *testing.T) {
		if got := lo.SumBy([]float64{0.1, 0.2}, func(f float64) float64 { return f }); got != 0.30000000000000004 {
			t.Errorf("0.1+0.2 = %v", got)
		}
		tenth := make([]float64, 10)
		for i := range tenth {
			tenth[i] = 0.1
		}
		if got := lo.SumBy(tenth, func(f float64) float64 { return f }); got != 0.9999999999999999 {
			t.Errorf("0.1×10 = %v", got)
		}
		if got := lo.SumBy([]float64{1, math.NaN()}, func(f float64) float64 { return f }); !math.IsNaN(got) {
			t.Errorf("NaN = %v", got)
		}
	})

	t.Run("iteratee の panic はそのまま伝播する", func(t *testing.T) {
		defer func() {
			if r := recover(); r != "boom" {
				t.Errorf("recover = %v", r)
			}
		}()
		lo.SumBy(items, func(i sumItem) int { panic("boom") })
	})
}
