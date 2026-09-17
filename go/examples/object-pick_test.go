// カード object-pick の Contract を検証するテスト
package examples

import (
	"reflect"
	"testing"

	"github.com/samber/lo"
)

func TestObjectPick(t *testing.T) {
	src := func() map[string]int { return map[string]int{"a": 1, "b": 2, "c": 3, "zero": 0} }

	t.Run("指定したキーだけを取り出し、存在しないキーは無視する", func(t *testing.T) {
		got := lo.PickByKeys(src(), []string{"a", "c", "zz"})
		if want := map[string]int{"a": 1, "c": 3}; !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("値がゼロ値でもエントリがあれば含まれる", func(t *testing.T) {
		got := lo.PickByKeys(src(), []string{"zero"})
		if v, ok := got["zero"]; !ok || v != 0 {
			t.Errorf("got %v", got)
		}
	})

	t.Run("keys の重複は 1 つにまとまる", func(t *testing.T) {
		got := lo.PickByKeys(src(), []string{"a", "a"})
		if len(got) != 1 || got["a"] != 1 {
			t.Errorf("got %v", got)
		}
	})

	t.Run("入力を変更せず、新しい map を返す（値は浅いコピー）", func(t *testing.T) {
		m := src()
		got := lo.PickByKeys(m, []string{"a"})
		got["a"] = 100
		got["new"] = 1
		if m["a"] != 1 || len(m) != 4 {
			t.Errorf("入力が変わった: %v", m)
		}
		nested := map[string][]int{"a": {1}}
		picked := lo.PickByKeys(nested, []string{"a"})
		picked["a"][0] = 99
		if nested["a"][0] != 99 {
			t.Errorf("スライス値は同じ参照先のはず: %v", nested)
		}
	})

	t.Run("keys が空・nil、入力が nil map でも空の非 nil map を返す", func(t *testing.T) {
		if got := lo.PickByKeys(src(), nil); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
		if got := lo.PickByKeys(map[string]int(nil), []string{"a"}); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
	})

	t.Run("返り値は入力と同じ名前付き map 型", func(t *testing.T) {
		type Config map[string]int
		got := lo.PickByKeys(Config{"a": 1}, []string{"a"})
		if _, ok := any(got).(Config); !ok {
			t.Errorf("型が %T", got)
		}
	})
}
