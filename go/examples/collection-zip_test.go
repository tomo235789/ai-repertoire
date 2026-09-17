// カード collection-zip の Contract を検証するテスト
package examples

import (
	"reflect"
	"slices"
	"testing"

	"github.com/samber/lo"
)

func TestCollectionZip(t *testing.T) {
	t.Run("同じ位置の要素を A / B に組む", func(t *testing.T) {
		got := lo.Zip2([]int{1, 2}, []string{"a", "b"})
		want := []lo.Tuple2[int, string]{{A: 1, B: "a"}, {A: 2, B: "b"}}
		if !reflect.DeepEqual(got, want) {
			t.Errorf("got %+v, want %+v", got, want)
		}
	})

	t.Run("長い方に合わせ、足りない位置はゼロ値で埋まる", func(t *testing.T) {
		got := lo.Zip2([]int{1, 2, 3}, []string{"a"})
		want := []lo.Tuple2[int, string]{{A: 1, B: "a"}, {A: 2, B: ""}, {A: 3, B: ""}}
		if !reflect.DeepEqual(got, want) {
			t.Errorf("got %+v, want %+v", got, want)
		}
		got2 := lo.Zip2([]int{1}, []*int{nil, nil})
		if len(got2) != 2 || got2[1].A != 0 {
			t.Errorf("got %+v", got2)
		}
	})

	t.Run("入力を変更しない", func(t *testing.T) {
		a, b := []int{1, 2}, []string{"a", "b"}
		got := lo.Zip2(a, b)
		got[0].A, got[0].B = 99, "z"
		if !slices.Equal(a, []int{1, 2}) || !slices.Equal(b, []string{"a", "b"}) {
			t.Errorf("入力が変わった: %v %v", a, b)
		}
	})

	t.Run("両方とも空・nil なら空の非 nil スライス", func(t *testing.T) {
		if got := lo.Zip2([]int{}, []string{}); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
		if got := lo.Zip2([]int(nil), []string(nil)); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
	})

	t.Run("Zip3 も同じ規則で、Unzip2 は逆操作", func(t *testing.T) {
		got := lo.Zip3([]int{1}, []string{"a", "b"}, []bool{})
		want := []lo.Tuple3[int, string, bool]{{A: 1, B: "a", C: false}, {A: 0, B: "b", C: false}}
		if !reflect.DeepEqual(got, want) {
			t.Errorf("got %+v, want %+v", got, want)
		}
		as, bs := lo.Unzip2(lo.Zip2([]int{1, 2}, []string{"a", "b"}))
		if !slices.Equal(as, []int{1, 2}) || !slices.Equal(bs, []string{"a", "b"}) {
			t.Errorf("unzip = %v %v", as, bs)
		}
	})
}
