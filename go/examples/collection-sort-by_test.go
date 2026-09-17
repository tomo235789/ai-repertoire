// カード collection-sort-by の Contract を検証するテスト
package examples

import (
	"cmp"
	"math"
	"reflect"
	"slices"
	"testing"
)

type sortUser struct {
	Name string
	Age  int
}

func TestCollectionSortBy(t *testing.T) {
	byAgeThenName := func(x, y sortUser) int {
		return cmp.Or(cmp.Compare(x.Age, y.Age), cmp.Compare(x.Name, y.Name))
	}

	t.Run("複数キーを左から順に比較して昇順に並べる", func(t *testing.T) {
		users := []sortUser{{"b", 30}, {"a", 20}, {"c", 30}, {"d", 20}}
		slices.SortStableFunc(users, byAgeThenName)
		want := []sortUser{{"a", 20}, {"d", 20}, {"b", 30}, {"c", 30}}
		if !reflect.DeepEqual(users, want) {
			t.Errorf("got %v, want %v", users, want)
		}
	})

	t.Run("安定ソート。キーが等しい要素は元の相対順を保つ", func(t *testing.T) {
		users := []sortUser{{"b", 30}, {"a", 20}, {"c", 30}, {"d", 20}}
		slices.SortStableFunc(users, func(x, y sortUser) int { return cmp.Compare(x.Age, y.Age) })
		want := []sortUser{{"a", 20}, {"d", 20}, {"b", 30}, {"c", 30}}
		if !reflect.DeepEqual(users, want) {
			t.Errorf("got %v, want %v", users, want)
		}
	})

	t.Run("破壊的で、元を残すには先に Clone する", func(t *testing.T) {
		src := []int{3, 1, 2}
		slices.SortStableFunc(src, cmp.Compare[int])
		if !slices.Equal(src, []int{1, 2, 3}) {
			t.Errorf("その場で並べ替わっていない: %v", src)
		}
		orig := []int{3, 1, 2}
		cloned := slices.Clone(orig)
		slices.SortStableFunc(cloned, cmp.Compare[int])
		if !slices.Equal(orig, []int{3, 1, 2}) || !slices.Equal(cloned, []int{1, 2, 3}) {
			t.Errorf("orig = %v, cloned = %v", orig, cloned)
		}
	})

	t.Run("引数を入れ替えると降順になり、キーごとに向きを変えられる", func(t *testing.T) {
		users := []sortUser{{"a", 20}, {"b", 30}, {"c", 30}}
		slices.SortStableFunc(users, func(x, y sortUser) int {
			return cmp.Or(cmp.Compare(y.Age, x.Age), cmp.Compare(x.Name, y.Name)) // Age 降順 → Name 昇順
		})
		want := []sortUser{{"b", 30}, {"c", 30}, {"a", 20}}
		if !reflect.DeepEqual(users, want) {
			t.Errorf("got %v, want %v", users, want)
		}
	})

	t.Run("比較関数は比較のたびに呼ばれる（各要素 1 回ではない）", func(t *testing.T) {
		calls := 0
		s := []int{5, 4, 3, 2, 1}
		slices.SortStableFunc(s, func(a, b int) int { calls++; return cmp.Compare(a, b) })
		if calls <= len(s) {
			t.Errorf("calls = %d, 要素数 %d 以下", calls, len(s))
		}
	})

	t.Run("cmp.Compare は NaN を最小として扱い、並びが定まる", func(t *testing.T) {
		s := []float64{2, math.NaN(), 1}
		slices.SortStableFunc(s, cmp.Compare[float64])
		if !math.IsNaN(s[0]) || s[1] != 1 || s[2] != 2 {
			t.Errorf("got %v", s)
		}
	})

	t.Run("空スライス・nil でも panic しない", func(t *testing.T) {
		var empty []int
		slices.SortStableFunc(empty, cmp.Compare[int])
		slices.SortStableFunc([]int{}, cmp.Compare[int])
		if empty != nil {
			t.Errorf("nil が変わった: %#v", empty)
		}
	})

	t.Run("SortedStableFunc は元を変えずに新しいスライスを返す", func(t *testing.T) {
		orig := []int{3, 1, 2}
		got := slices.SortedStableFunc(slices.Values(orig), cmp.Compare[int])
		if !slices.Equal(orig, []int{3, 1, 2}) || !slices.Equal(got, []int{1, 2, 3}) {
			t.Errorf("orig = %v, got = %v", orig, got)
		}
	})
}
