// カード object-map-values の Contract を検証するテスト
package examples

import (
	"fmt"
	"reflect"
	"slices"
	"testing"

	"github.com/samber/lo"
)

func TestObjectMapValues(t *testing.T) {
	t.Run("同じキーで値だけを変換した新しい map を返す", func(t *testing.T) {
		prices := map[string]int{"apple": 100, "pear": 250}
		got := lo.MapValues(prices, func(v int, k string) string { return fmt.Sprintf("%d円", v) })
		if want := map[string]string{"apple": "100円", "pear": "250円"}; !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("入力を変更しない。入力の値をそのまま返せば同じ参照先", func(t *testing.T) {
		m := map[string]int{"a": 1}
		got := lo.MapValues(m, func(v int, _ string) int { return v * 10 })
		got["a"] = 0
		if m["a"] != 1 {
			t.Errorf("入力が変わった: %v", m)
		}
		nested := map[string][]int{"a": {1}}
		same := lo.MapValues(nested, func(v []int, _ string) []int { return v })
		same["a"][0] = 99
		if nested["a"][0] != 99 {
			t.Errorf("同じ参照先のはず: %v", nested)
		}
	})

	t.Run("iteratee は (value, key) の順で各エントリにつき 1 回呼ばれる", func(t *testing.T) {
		var keys []string
		lo.MapValues(map[string]int{"a": 1, "b": 2, "c": 3}, func(v int, k string) int {
			if fmt.Sprintf("%c", 'a'+v-1) != k { // 値とキーの対応で引数順を確認する
				t.Errorf("引数の対応が違う: v=%d k=%s", v, k)
			}
			keys = append(keys, k)
			return v
		})
		slices.Sort(keys)
		if !slices.Equal(keys, []string{"a", "b", "c"}) {
			t.Errorf("呼び出し = %v", keys)
		}
	})

	t.Run("空・nil の map は空の非 nil map を返す", func(t *testing.T) {
		f := func(v int, _ string) int { return v }
		if got := lo.MapValues(map[string]int{}, f); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
		if got := lo.MapValues(map[string]int(nil), f); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
	})

	t.Run("返り値は名前付き map 型を引き継がず素の map[K]R", func(t *testing.T) {
		type Config map[string]int
		got := lo.MapValues(Config{"a": 1}, func(v int, _ string) int { return v })
		if _, ok := any(got).(Config); ok {
			t.Errorf("名前付き型が引き継がれている: %T", got)
		}
		if _, ok := any(got).(map[string]int); !ok {
			t.Errorf("型が %T", got)
		}
	})
}
