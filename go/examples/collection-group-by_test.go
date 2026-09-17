// カード collection-group-by の Contract を検証するテスト
package examples

import (
	"maps"
	"reflect"
	"slices"
	"strings"
	"testing"

	"github.com/samber/lo"
)

func TestCollectionGroupBy(t *testing.T) {
	parity := func(n int) string {
		if n%2 == 0 {
			return "even"
		}
		return "odd"
	}

	t.Run("各グループは出現順のまま", func(t *testing.T) {
		got := lo.GroupBy([]int{1, 2, 3, 4, 5}, parity)
		want := map[string][]int{"even": {2, 4}, "odd": {1, 3, 5}}
		if !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("キーの順序が要るなら並べ替える（cmp.Ordered なら slices.Sorted(maps.Keys)）", func(t *testing.T) {
		got := lo.GroupBy([]int{1, 2, 3}, parity)
		if keys := slices.Sorted(maps.Keys(got)); !slices.Equal(keys, []string{"even", "odd"}) {
			t.Errorf("keys = %v", keys)
		}
		keys := slices.SortedFunc(maps.Keys(got), func(a, b string) int { return strings.Compare(b, a) })
		if !slices.Equal(keys, []string{"odd", "even"}) {
			t.Errorf("SortedFunc keys = %v", keys)
		}
	})

	t.Run("入力を変更せず、各グループは新しいスライス", func(t *testing.T) {
		src := []int{1, 2, 3}
		got := lo.GroupBy(src, func(int) int { return 0 })
		got[0][0] = 99
		if !slices.Equal(src, []int{1, 2, 3}) {
			t.Errorf("入力が変わった: %v", src)
		}
	})

	t.Run("キー関数は各要素につき 1 回、先頭から順に呼ばれる", func(t *testing.T) {
		var seen []int
		lo.GroupBy([]int{3, 1, 3}, func(n int) int {
			seen = append(seen, n)
			return n
		})
		if !slices.Equal(seen, []int{3, 1, 3}) {
			t.Errorf("呼び出し順 = %v", seen)
		}
	})

	t.Run("空スライス・nil は空の非 nil map を返す", func(t *testing.T) {
		if got := lo.GroupBy([]int{}, parity); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
		if got := lo.GroupBy([]int(nil), parity); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
	})

	t.Run("存在しないキーは nil スライスで panic しない", func(t *testing.T) {
		got := lo.GroupBy([]int{1}, parity)
		if g := got["none"]; g != nil || len(g) != 0 {
			t.Errorf("got %#v", g)
		}
	})

	t.Run("各グループは入力と同じ名前付きスライス型", func(t *testing.T) {
		type IDs []int
		got := lo.GroupBy(IDs{1, 2}, parity)
		if _, ok := any(got["odd"]).(IDs); !ok {
			t.Errorf("型が %T", got["odd"])
		}
	})

	t.Run("interface キーで動的な型がスライスだと実行時に panic する", func(t *testing.T) {
		identity := func(x any) any { return x }
		if got := lo.GroupBy([]any{1, "a", 1}, identity); len(got) != 2 {
			t.Errorf("比較可能な動的型なら動く: %v", got)
		}
		defer func() {
			if r := recover(); r == nil {
				t.Errorf("panic しなかった")
			}
		}()
		lo.GroupBy([]any{[]int{1}}, identity)
	})
}
