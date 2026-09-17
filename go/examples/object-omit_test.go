// カード object-omit の Contract を検証するテスト
package examples

import (
	"reflect"
	"testing"

	"github.com/samber/lo"
)

func TestObjectOmit(t *testing.T) {
	src := func() map[string]string { return map[string]string{"name": "alice", "password": "x", "role": "admin"} }

	t.Run("指定したキーを除き、存在しないキーは無視する", func(t *testing.T) {
		got := lo.OmitByKeys(src(), []string{"password", "zz"})
		if want := map[string]string{"name": "alice", "role": "admin"}; !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("入力を変更せず、新しい map を返す（値は浅いコピー）", func(t *testing.T) {
		m := src()
		got := lo.OmitByKeys(m, []string{"password"})
		got["name"] = "bob"
		if m["name"] != "alice" || len(m) != 3 {
			t.Errorf("入力が変わった: %v", m)
		}
		nested := map[string][]int{"a": {1}, "b": {2}}
		omitted := lo.OmitByKeys(nested, []string{"b"})
		omitted["a"][0] = 99
		if nested["a"][0] != 99 {
			t.Errorf("スライス値は同じ参照先のはず: %v", nested)
		}
	})

	t.Run("すべて除くと空の非 nil map、keys が空なら同じ内容の別 map", func(t *testing.T) {
		if got := lo.OmitByKeys(src(), []string{"name", "password", "role"}); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
		m := src()
		got := lo.OmitByKeys(m, nil)
		if !reflect.DeepEqual(got, m) {
			t.Errorf("got %v", got)
		}
		got["name"] = "bob"
		if m["name"] != "alice" {
			t.Errorf("同じ map を返している")
		}
	})

	t.Run("入力が nil map でも空の非 nil map を返す", func(t *testing.T) {
		if got := lo.OmitByKeys(map[string]string(nil), []string{"a"}); got == nil || len(got) != 0 {
			t.Errorf("got %#v", got)
		}
	})

	t.Run("返り値は入力と同じ名前付き map 型", func(t *testing.T) {
		type Config map[string]string
		got := lo.OmitByKeys(Config{"a": "1"}, []string{"a"})
		if _, ok := any(got).(Config); !ok {
			t.Errorf("型が %T", got)
		}
	})
}
