// カード collection-take-while の Contract を検証するテスト
package examples

import (
	"slices"
	"testing"

	"github.com/samber/lo"
)

func TestCollectionTakeWhile(t *testing.T) {
	lessThan3 := func(n int) bool { return n < 3 }

	t.Run("先頭から真の間だけ取り出し、最初の偽で打ち切る", func(t *testing.T) {
		if got := lo.TakeWhile([]int{1, 2, 3, 1, 2}, lessThan3); !slices.Equal(got, []int{1, 2}) {
			t.Errorf("got %v", got)
		}
	})

	t.Run("入力を変更せず、新しいスライスを返す", func(t *testing.T) {
		src := []int{1, 2}
		got := lo.TakeWhile(src, lessThan3)
		got[0] = 99
		if !slices.Equal(src, []int{1, 2}) {
			t.Errorf("入力が変わった: %v", src)
		}
	})

	t.Run("述語は最初に偽を返した要素まで呼ばれ、それ以降は呼ばれない", func(t *testing.T) {
		var seen []int
		lo.TakeWhile([]int{1, 2, 3, 1, 1}, func(n int) bool {
			seen = append(seen, n)
			return n < 3
		})
		if !slices.Equal(seen, []int{1, 2, 3}) {
			t.Errorf("呼び出し = %v", seen)
		}
	})

	t.Run("すべて真なら全要素、先頭で偽なら空の非 nil", func(t *testing.T) {
		if got := lo.TakeWhile([]int{1, 2}, lessThan3); !slices.Equal(got, []int{1, 2}) {
			t.Errorf("got %v", got)
		}
		if got := lo.TakeWhile([]int{5, 1}, lessThan3); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
	})

	t.Run("空スライス・nil は空の非 nil スライス", func(t *testing.T) {
		if got := lo.TakeWhile([]int{}, lessThan3); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
		if got := lo.TakeWhile([]int(nil), lessThan3); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
	})

	t.Run("返り値は入力と同じ名前付きスライス型", func(t *testing.T) {
		type IDs []int
		got := lo.TakeWhile(IDs{1}, lessThan3)
		if _, ok := any(got).(IDs); !ok {
			t.Errorf("型が %T", got)
		}
	})

	t.Run("DropWhile と連結すると元に戻る", func(t *testing.T) {
		src := []int{1, 2, 3, 1}
		got := slices.Concat(lo.TakeWhile(src, lessThan3), lo.DropWhile(src, lessThan3))
		if !slices.Equal(got, src) {
			t.Errorf("got %v", got)
		}
	})
}
