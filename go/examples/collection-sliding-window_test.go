// カード collection-sliding-window の Contract を検証するテスト
package examples

import (
	"reflect"
	"slices"
	"testing"

	"github.com/samber/lo"
)

func TestCollectionSlidingWindow(t *testing.T) {
	t.Run("1 つずつずらした窓を順に返し、窓の中も元の並び順", func(t *testing.T) {
		got := lo.Window([]int{1, 2, 3, 4}, 2)
		want := [][]int{{1, 2}, {2, 3}, {3, 4}}
		if !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("入力を変更せず、各窓は独立したコピー", func(t *testing.T) {
		src := []int{1, 2, 3}
		got := lo.Window(src, 2)
		got[0][1] = 99
		if !slices.Equal(src, []int{1, 2, 3}) {
			t.Errorf("入力が変わった: %v", src)
		}
		if !slices.Equal(got[1], []int{2, 3}) {
			t.Errorf("隣の窓が変わった: %v", got[1])
		}
	})

	t.Run("size に満たない末尾の窓は作られず、長さが size 未満なら空の非 nil", func(t *testing.T) {
		if got := lo.Window([]int{1, 2}, 3); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
		if got := lo.Window([]int{1, 2}, 2); !reflect.DeepEqual(got, [][]int{{1, 2}}) {
			t.Errorf("got %v", got)
		}
	})

	t.Run("空スライス・nil は空の非 nil スライス", func(t *testing.T) {
		if got := lo.Window([]int{}, 2); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
		if got := lo.Window([]int(nil), 1); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
	})

	t.Run("size <= 0 は panic する", func(t *testing.T) {
		for _, size := range []int{0, -1} {
			func() {
				defer func() {
					if recover() == nil {
						t.Errorf("size=%d で panic しない", size)
					}
				}()
				_ = lo.Window([]int{1, 2}, size)
			}()
		}
	})

	t.Run("各窓は入力と同じ名前付きスライス型", func(t *testing.T) {
		type IDs []int
		got := lo.Window(IDs{1, 2}, 1)
		if _, ok := any(got[0]).(IDs); !ok {
			t.Errorf("型が %T", got[0])
		}
	})

	t.Run("Sliding は step 指定で、飛ばした要素と末尾の不完全な窓は捨てられる", func(t *testing.T) {
		if got := lo.Sliding([]int{1, 2, 3, 4, 5}, 2, 2); !reflect.DeepEqual(got, [][]int{{1, 2}, {3, 4}}) {
			t.Errorf("got %v", got)
		}
		if got := lo.Sliding([]int{1, 2, 3, 4, 5}, 2, 3); !reflect.DeepEqual(got, [][]int{{1, 2}, {4, 5}}) {
			t.Errorf("got %v", got)
		}
	})
}
