// カード collection-partition の Contract を検証するテスト
package examples

import (
	"slices"
	"testing"

	"github.com/samber/lo"
)

func TestCollectionPartition(t *testing.T) {
	isEven := func(n int, _ int) bool { return n%2 == 0 }

	t.Run("真が先、偽が後で、どちらも順序を保つ", func(t *testing.T) {
		kept, rejected := lo.FilterReject([]int{1, 2, 3, 4, 5}, isEven)
		if !slices.Equal(kept, []int{2, 4}) || !slices.Equal(rejected, []int{1, 3, 5}) {
			t.Errorf("kept = %v, rejected = %v", kept, rejected)
		}
	})

	t.Run("入力を変更せず、新しいスライスを返す", func(t *testing.T) {
		src := []int{1, 2, 3}
		kept, rejected := lo.FilterReject(src, isEven)
		kept[0] = 99
		rejected[0] = 99
		if !slices.Equal(src, []int{1, 2, 3}) {
			t.Errorf("入力が変わった: %v", src)
		}
	})

	t.Run("述語は (要素, 添字) で各要素につき 1 回、先頭から順に呼ばれる", func(t *testing.T) {
		var items, indexes []int
		lo.FilterReject([]int{10, 20, 30}, func(n int, i int) bool {
			items = append(items, n)
			indexes = append(indexes, i)
			return true
		})
		if !slices.Equal(items, []int{10, 20, 30}) || !slices.Equal(indexes, []int{0, 1, 2}) {
			t.Errorf("items = %v, indexes = %v", items, indexes)
		}
	})

	t.Run("すべて真・すべて偽でも空側は非 nil", func(t *testing.T) {
		kept, rejected := lo.FilterReject([]int{2, 4}, isEven)
		if !slices.Equal(kept, []int{2, 4}) || rejected == nil || len(rejected) != 0 {
			t.Errorf("kept = %v, rejected = %#v", kept, rejected)
		}
	})

	t.Run("空スライス・nil は両方とも空の非 nil スライス", func(t *testing.T) {
		for _, in := range [][]int{{}, nil} {
			kept, rejected := lo.FilterReject(in, isEven)
			if kept == nil || rejected == nil || len(kept) != 0 || len(rejected) != 0 {
				t.Errorf("in=%#v: kept = %#v, rejected = %#v", in, kept, rejected)
			}
		}
	})

	t.Run("返り値は入力と同じ名前付きスライス型", func(t *testing.T) {
		type IDs []int
		kept, rejected := lo.FilterReject(IDs{1, 2}, isEven)
		if _, ok := any(kept).(IDs); !ok {
			t.Errorf("kept の型が %T", kept)
		}
		if _, ok := any(rejected).(IDs); !ok {
			t.Errorf("rejected の型が %T", rejected)
		}
	})
}
