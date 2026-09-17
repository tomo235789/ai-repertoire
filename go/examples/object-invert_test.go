// カード object-invert の Contract を検証するテスト
package examples

import (
	"reflect"
	"testing"

	"github.com/samber/lo"
)

func TestObjectInvert(t *testing.T) {
	t.Run("キーと値を入れ替えた新しい map を返し、型はそのまま", func(t *testing.T) {
		got := lo.Invert(map[string]int{"apple": 1, "pear": 2})
		if want := map[int]string{1: "apple", 2: "pear"}; !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("入力を変更しない", func(t *testing.T) {
		m := map[string]int{"a": 1}
		got := lo.Invert(m)
		got[1] = "changed"
		got[2] = "new"
		if m["a"] != 1 || len(m) != 1 {
			t.Errorf("入力が変わった: %v", m)
		}
	})

	t.Run("値が重複するとエントリ数が減り、残るのは元のキーのどれか", func(t *testing.T) {
		dup := map[string]int{"a": 1, "b": 1, "c": 1}
		inv := lo.Invert(dup)
		if len(inv) != 1 {
			t.Fatalf("len = %d, want 1", len(inv))
		}
		if _, ok := dup[inv[1]]; !ok {
			t.Errorf("残ったキー %q は元の map に無い", inv[1])
		}
	})

	t.Run("len の比較で重複を検出できる", func(t *testing.T) {
		m := map[string]int{"a": 1, "b": 1}
		if inv := lo.Invert(m); len(inv) == len(m) {
			t.Errorf("重複が検出されない: %v", inv)
		}
	})

	t.Run("空・nil の map は空の非 nil map を返す", func(t *testing.T) {
		if got := lo.Invert(map[string]int{}); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
		if got := lo.Invert(map[string]int(nil)); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
	})
}
