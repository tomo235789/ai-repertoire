// カード collection-flatten の Contract を検証するテスト
package examples

import (
	"reflect"
	"slices"
	"testing"

	"github.com/samber/lo"
)

func TestCollectionFlatten(t *testing.T) {
	t.Run("外側・内側の順序を保って 1 段開く", func(t *testing.T) {
		nested := [][]int{{1, 2}, {3}, {}, {4, 5}}
		if got := slices.Concat(nested...); !slices.Equal(got, []int{1, 2, 3, 4, 5}) {
			t.Errorf("got %v", got)
		}
	})

	t.Run("入力を変更せず、新しいスライスを返す（引数 1 つでもコピー）", func(t *testing.T) {
		a, b := []int{1, 2}, []int{3}
		got := slices.Concat(a, b)
		got[0] = 99
		if !slices.Equal(a, []int{1, 2}) {
			t.Errorf("入力が変わった: %v", a)
		}
		one := slices.Concat(a)
		one[0] = 77
		if a[0] != 1 {
			t.Errorf("引数 1 つでもコピーされるはず: %v", a)
		}
	})

	t.Run("開くのは 1 段だけで、残った内側スライスは元と配列を共有する", func(t *testing.T) {
		nested := [][][]int{{{1, 2}}, {{3}}}
		got := slices.Concat(nested...)
		if !reflect.DeepEqual(got, [][]int{{1, 2}, {3}}) {
			t.Errorf("got %v", got)
		}
		got[0][0] = 99
		if nested[0][0][0] != 99 {
			t.Errorf("内側スライスが共有されていない: %v", nested)
		}
	})

	t.Run("引数なし・すべて空なら nil、nil が混ざっても panic しない", func(t *testing.T) {
		if got := slices.Concat[[]int](); got != nil {
			t.Errorf("got %#v", got)
		}
		if got := slices.Concat([]int{}, nil); got != nil {
			t.Errorf("got %#v", got)
		}
		if got := slices.Concat([]int{1}, nil, []int{2}); !slices.Equal(got, []int{1, 2}) {
			t.Errorf("got %v", got)
		}
	})

	t.Run("返り値は入力と同じ名前付きスライス型", func(t *testing.T) {
		type IDs []int
		got := slices.Concat(IDs{1}, IDs{2})
		if _, ok := any(got).(IDs); !ok {
			t.Errorf("型が %T", got)
		}
	})

	t.Run("lo.Flatten は空入力で非 nil の空スライスを返す", func(t *testing.T) {
		if got := lo.Flatten([][]int{}); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
		if got := lo.Flatten([][]int{{1}, {2, 3}}); !slices.Equal(got, []int{1, 2, 3}) {
			t.Errorf("got %v", got)
		}
	})
}
