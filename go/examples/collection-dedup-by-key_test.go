// カード collection-dedup-by-key の Contract を検証するテスト
package examples

import (
	"math"
	"reflect"
	"testing"

	"github.com/samber/lo"
)

type dedupUser struct {
	ID   int
	Name string
}

func TestCollectionDedupByKey(t *testing.T) {
	byID := func(u dedupUser) int { return u.ID }

	t.Run("順序を保ち、同じキーは最初の要素を残す", func(t *testing.T) {
		users := []dedupUser{{1, "a"}, {2, "b"}, {1, "c"}, {3, "d"}, {2, "e"}}
		got := lo.UniqBy(users, byID)
		want := []dedupUser{{1, "a"}, {2, "b"}, {3, "d"}}
		if !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("入力を変更せず、新しいスライスを返す", func(t *testing.T) {
		users := []dedupUser{{1, "a"}, {1, "b"}}
		got := lo.UniqBy(users, byID)
		got[0].Name = "changed"
		if !reflect.DeepEqual(users, []dedupUser{{1, "a"}, {1, "b"}}) {
			t.Errorf("入力が変わった: %v", users)
		}
	})

	t.Run("キー関数は各要素につき 1 回、先頭から順に呼ばれる", func(t *testing.T) {
		var seen []int
		lo.UniqBy([]dedupUser{{3, ""}, {1, ""}, {3, ""}}, func(u dedupUser) int {
			seen = append(seen, u.ID)
			return u.ID
		})
		if !reflect.DeepEqual(seen, []int{3, 1, 3}) {
			t.Errorf("呼び出し順 = %v", seen)
		}
	})

	t.Run("キーは == で比較され、NaN は毎回別扱い", func(t *testing.T) {
		nan := math.NaN()
		got := lo.UniqBy([]float64{nan, nan, 1, 1}, func(f float64) float64 { return f })
		if len(got) != 3 {
			t.Errorf("len = %d, want 3", len(got))
		}
	})

	t.Run("空スライス・nil は空の非 nil スライスを返す", func(t *testing.T) {
		if got := lo.UniqBy([]dedupUser{}, byID); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
		if got := lo.UniqBy([]dedupUser(nil), byID); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
	})

	t.Run("返り値は入力と同じ名前付きスライス型", func(t *testing.T) {
		type Users []dedupUser
		got := lo.UniqBy(Users{{1, "a"}}, byID)
		if _, ok := any(got).(Users); !ok {
			t.Errorf("型が %T", got)
		}
	})

	t.Run("interface キーで動的な型がスライスだと実行時に panic する", func(t *testing.T) {
		identity := func(x any) any { return x }
		if got := lo.UniqBy([]any{1, "a", 1}, identity); len(got) != 2 {
			t.Errorf("比較可能な動的型なら動く: %v", got)
		}
		defer func() {
			if r := recover(); r == nil {
				t.Errorf("panic しなかった")
			}
		}()
		lo.UniqBy([]any{[]int{1}}, identity)
	})
}
