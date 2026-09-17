// カード collection-chunk の Contract を検証するテスト
package examples

import (
	"reflect"
	"slices"
	"testing"
)

func TestCollectionChunk(t *testing.T) {
	t.Run("順序を保ったまま n ごとに分割し、最後は短くなる", func(t *testing.T) {
		got := slices.Collect(slices.Chunk([]int{1, 2, 3, 4, 5}, 2))
		want := [][]int{{1, 2}, {3, 4}, {5}}
		if !reflect.DeepEqual(got, want) {
			t.Errorf("got %v, want %v", got, want)
		}
	})

	t.Run("割り切れるときは最後も n 個、n が長さ以上なら全体が 1 つ", func(t *testing.T) {
		if got := slices.Collect(slices.Chunk([]int{1, 2, 3, 4}, 2)); !reflect.DeepEqual(got, [][]int{{1, 2}, {3, 4}}) {
			t.Errorf("got %v", got)
		}
		if got := slices.Collect(slices.Chunk([]int{1, 2, 3}, 10)); !reflect.DeepEqual(got, [][]int{{1, 2, 3}}) {
			t.Errorf("got %v", got)
		}
	})

	t.Run("イテレータは途中で break でき、何度でも走査できる", func(t *testing.T) {
		seq := slices.Chunk([]int{1, 2, 3, 4, 5}, 2)
		var first []int
		for c := range seq {
			first = c
			break
		}
		if !slices.Equal(first, []int{1, 2}) {
			t.Errorf("first = %v", first)
		}
		if a, b := slices.Collect(seq), slices.Collect(seq); !reflect.DeepEqual(a, b) || len(a) != 3 {
			t.Errorf("2 回目の走査が一致しない: %v / %v", a, b)
		}
	})

	t.Run("部分スライスは元の配列を共有するビュー", func(t *testing.T) {
		src := []int{1, 2, 3, 4, 5}
		chunks := slices.Collect(slices.Chunk(src, 2))
		if !slices.Equal(src, []int{1, 2, 3, 4, 5}) {
			t.Errorf("Chunk 自体が入力を変えた: %v", src)
		}
		chunks[0][0] = 99
		if src[0] != 99 {
			t.Errorf("部分スライスの書き換えが元に反映されない: %v", src)
		}
	})

	t.Run("cap は長さに切り詰められ、append しても元の後続要素を上書きしない", func(t *testing.T) {
		src := []int{1, 2, 3, 4, 5}
		chunks := slices.Collect(slices.Chunk(src, 2))
		if cap(chunks[0]) != 2 || cap(chunks[2]) != 1 {
			t.Errorf("cap = %d, %d", cap(chunks[0]), cap(chunks[2]))
		}
		_ = append(chunks[0], 100)
		if !slices.Equal(src, []int{1, 2, 3, 4, 5}) {
			t.Errorf("append が元を上書きした: %v", src)
		}
	})

	t.Run("空スライス・nil は何も返さず Collect は nil", func(t *testing.T) {
		if got := slices.Collect(slices.Chunk([]int{}, 3)); got != nil {
			t.Errorf("got %v", got)
		}
		if got := slices.Collect(slices.Chunk([]int(nil), 3)); got != nil {
			t.Errorf("got %v", got)
		}
	})

	t.Run("n < 1 なら呼んだ時点で panic する", func(t *testing.T) {
		for _, n := range []int{0, -1} {
			func() {
				defer func() {
					if recover() == nil {
						t.Errorf("n=%d で panic しない", n)
					}
				}()
				_ = slices.Chunk([]int{1, 2}, n) // イテレーションせずに呼ぶだけ
			}()
		}
	})

	t.Run("返り値は入力と同じ名前付きスライス型", func(t *testing.T) {
		type IDs []int
		got := slices.Collect(slices.Chunk(IDs{1, 2, 3}, 2))
		if _, ok := any(got[0]).(IDs); !ok {
			t.Errorf("型が %T", got[0])
		}
	})
}
